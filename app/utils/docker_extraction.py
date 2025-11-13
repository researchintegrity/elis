"""
Docker-based PDF image extraction using pdf-extractor container
"""
import subprocess
import os
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)


def extract_images_with_docker(
    doc_id: str,
    user_id: str,
    pdf_file_path: str,
    docker_image: str = "pdf-extractor:latest"
) -> Tuple[int, List[str]]:
    """
    Extract images from PDF using Docker container
    
    Runs the pdf-extractor Docker container to extract images from a PDF file.
    The container will process the PDF and save extracted images to the output directory.
    
    Docker Command:
        docker run \\
            -v $(pwd):/INPUT \\
            -v $(pwd)/output:/OUTPUT \\
            -e INPUT_PATH=/INPUT/sample.pdf \\
            -e OUTPUT_PATH=/OUTPUT \\
            pdf-extractor:latest
    
    Output Flow:
        Extracting images from: /INPUT/sample_1.pdf
        Mode: normal
        Output: /OUTPUT
    
    Args:
        doc_id: Document ID for tracking
        user_id: User ID for workspace organization
        pdf_file_path: Full path to the PDF file
        docker_image: Docker image to use (default: pdf-extractor:latest)
        
    Returns:
        Tuple of (extracted_image_count, extraction_errors)
        - extracted_image_count: Number of images successfully extracted
        - extraction_errors: List of error messages encountered
        
    Raises:
        Returns errors in list instead of raising exceptions
    """
    extraction_errors = []
    extracted_image_count = 0
    
    try:
        # Validate PDF file exists
        if not os.path.exists(pdf_file_path):
            error_msg = f"PDF file not found: {pdf_file_path}"
            logger.error(error_msg)
            return 0, [error_msg]
        
        # Get extraction output path
        from app.utils.file_storage import get_extraction_output_path
        output_dir = get_extraction_output_path(user_id, doc_id)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the directory containing the PDF
        pdf_dir = os.path.dirname(pdf_file_path)
        pdf_filename = os.path.basename(pdf_file_path)
        
        logger.info(
            f"Starting Docker extraction for doc_id={doc_id}\n"
            f"  PDF: {pdf_file_path}\n"
            f"  Input dir: {pdf_dir}\n"
            f"  Output dir: {output_dir}"
        )
        
        # Build Docker command
        docker_command = [
            "docker", "run",
            "--rm",  # Remove container after execution
            "-v", f"{pdf_dir}:/INPUT",  # Volume mount for PDF input
            "-v", f"{output_dir}:/OUTPUT",  # Volume mount for extracted images
            "-e", f"INPUT_PATH=/INPUT/{pdf_filename}",  # Environment variable for input file
            "-e", "OUTPUT_PATH=/OUTPUT",  # Environment variable for output directory
            docker_image  # Docker image name
        ]
        
        logger.info(f"Executing Docker command: {' '.join(docker_command)}")
        
        # Execute Docker container
        result = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        # Log Docker output
        if result.stdout:
            logger.info(f"Docker stdout:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Docker stderr:\n{result.stderr}")
        
        # Check if Docker command succeeded
        if result.returncode != 0:
            error_msg = f"Docker extraction failed with return code {result.returncode}"
            logger.error(error_msg)
            if result.stderr:
                extraction_errors.append(f"{error_msg}: {result.stderr}")
            else:
                extraction_errors.append(error_msg)
            return 0, extraction_errors
        
        # Count extracted images in output directory
        if os.path.exists(output_dir):
            extracted_files = [
                f for f in os.listdir(output_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.tiff', '.bmp'))
            ]
            extracted_image_count = len(extracted_files)
            
            logger.info(
                f"Docker extraction completed for doc_id={doc_id}\n"
                f"  Extracted images: {extracted_image_count}\n"
                f"  Files: {extracted_files}"
            )
        else:
            error_msg = f"Output directory not created: {output_dir}"
            logger.warning(error_msg)
            extraction_errors.append(error_msg)
        
        return extracted_image_count, extraction_errors
        
    except subprocess.TimeoutExpired:
        error_msg = f"Docker extraction timeout for doc_id={doc_id} (5 minutes)"
        logger.error(error_msg)
        extraction_errors.append(error_msg)
        return 0, extraction_errors
        
    except Exception as exc:
        error_msg = f"Docker extraction error for doc_id={doc_id}: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        extraction_errors.append(error_msg)
        return 0, extraction_errors


def extract_images_with_docker_compose(
    doc_id: str,
    user_id: str,
    pdf_file_path: str,
    service_name: str = "pdf-extractor"
) -> Tuple[int, List[str]]:
    """
    Extract images from PDF using Docker Compose service
    
    Alternative method using docker-compose if the service is defined in docker-compose.yml
    
    Args:
        doc_id: Document ID for tracking
        user_id: User ID for workspace organization
        pdf_file_path: Full path to the PDF file
        service_name: Name of the service in docker-compose.yml
        
    Returns:
        Tuple of (extracted_image_count, extraction_errors)
    """
    extraction_errors = []
    extracted_image_count = 0
    
    try:
        # Validate PDF file exists
        if not os.path.exists(pdf_file_path):
            error_msg = f"PDF file not found: {pdf_file_path}"
            logger.error(error_msg)
            return 0, [error_msg]
        
        # Get extraction output path
        from app.utils.file_storage import get_extraction_output_path
        output_dir = get_extraction_output_path(user_id, doc_id)
        os.makedirs(output_dir, exist_ok=True)
        
        pdf_dir = os.path.dirname(pdf_file_path)
        pdf_filename = os.path.basename(pdf_file_path)
        
        logger.info(
            f"Starting Docker Compose extraction for doc_id={doc_id}\n"
            f"  Service: {service_name}\n"
            f"  PDF: {pdf_file_path}"
        )
        
        # Build docker-compose command
        docker_compose_command = [
            "docker-compose", "run",
            "--rm",
            "-v", f"{pdf_dir}:/INPUT",
            "-v", f"{output_dir}:/OUTPUT",
            "-e", f"INPUT_PATH=/INPUT/{pdf_filename}",
            "-e", "OUTPUT_PATH=/OUTPUT",
            service_name
        ]
        
        logger.info(f"Executing: {' '.join(docker_compose_command)}")
        
        # Execute Docker Compose
        result = subprocess.run(
            docker_compose_command,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            error_msg = f"Docker Compose extraction failed: {result.stderr}"
            logger.error(error_msg)
            extraction_errors.append(error_msg)
            return 0, extraction_errors
        
        # Count extracted images
        if os.path.exists(output_dir):
            extracted_files = [
                f for f in os.listdir(output_dir)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.tiff', '.bmp'))
            ]
            extracted_image_count = len(extracted_files)
            logger.info(f"Extracted {extracted_image_count} images")
        
        return extracted_image_count, extraction_errors
        
    except subprocess.TimeoutExpired:
        error_msg = f"Docker Compose extraction timeout for doc_id={doc_id}"
        logger.error(error_msg)
        return 0, [error_msg]
        
    except Exception as exc:
        error_msg = f"Docker Compose extraction error: {str(exc)}"
        logger.error(error_msg, exc_info=True)
        return 0, [error_msg]


def verify_docker_image_exists(image_name: str = "pdf-extractor:latest") -> bool:
    """
    Verify if Docker image exists locally
    
    Args:
        image_name: Docker image name (default: pdf-extractor:latest)
        
    Returns:
        True if image exists, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            capture_output=True,
            timeout=10
        )
        exists = result.returncode == 0
        if exists:
            logger.info(f"Docker image found: {image_name}")
        else:
            logger.warning(f"Docker image not found: {image_name}")
        return exists
    except Exception as exc:
        logger.error(f"Error checking Docker image: {str(exc)}")
        return False


def get_docker_info() -> dict:
    """
    Get Docker information and status
    
    Returns:
        Dictionary with Docker info (version, running status, etc)
    """
    info = {
        "docker_available": False,
        "docker_version": None,
        "error": None
    }
    
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            info["docker_available"] = True
            info["docker_version"] = result.stdout.strip()
            logger.info(f"Docker available: {result.stdout.strip()}")
        else:
            info["error"] = "Docker not available or not running"
            logger.warning(info["error"])
            
    except Exception as exc:
        info["error"] = str(exc)
        logger.error(f"Error getting Docker info: {str(exc)}")
    
    return info
