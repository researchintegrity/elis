"""
Docker-based PDF watermark removal using pdf-watermark-removal container
"""
import subprocess
import os
import logging
from typing import Tuple, List, Dict
from app.config.settings import (
    DOCKER_EXTRACTION_TIMEOUT,
    DOCKER_IMAGE_CHECK_TIMEOUT,
    APP_WORKSPACE_PREFIX,
    is_container_path,
    get_container_path_length,
)

logger = logging.getLogger(__name__)

# Docker image name for watermark removal
PDF_WATERMARK_REMOVAL_DOCKER_IMAGE = "pdf-watermark-removal:latest"


def remove_watermark_with_docker(
    doc_id: str,
    user_id: str,
    pdf_file_path: str,
    aggressiveness_mode: int = 2,
    docker_image: str = None
) -> Tuple[bool, str, Dict]:
    """
    Remove watermark from PDF using Docker container
    
    Runs the pdf-watermark-removal Docker container to remove watermarks from a PDF file.
    The container will process the PDF and save the cleaned version to the output directory.
    
    Docker Command:
        docker run \\
            -v $(pwd):/workspace \\
            pdf-watermark-removal:latest \\
            -i /workspace/input.pdf \\
            -o /workspace/output.pdf \\
            -m 2
    
    Args:
        doc_id: Document ID for tracking
        user_id: User ID for workspace organization
        pdf_file_path: Full path to the PDF file
        aggressiveness_mode: Watermark removal aggressiveness (1, 2, or 3)
                           1 = explicit watermarks only
                           2 = text + repeated graphics (default)
                           3 = all graphics (most aggressive)
        docker_image: Docker image to use (default: pdf-watermark-removal:latest)
        
    Returns:
        Tuple of (success, status_message, output_file_info)
        - success: Boolean indicating if removal was successful
        - status_message: Human-readable status or error message
        - output_file_info: Dict with file info {filename, path, size, status}
        
    Raises:
        Returns errors in tuple format instead of raising exceptions
    """
    output_file_info = {}
    
    # Use default Docker image if not specified
    if docker_image is None:
        docker_image = PDF_WATERMARK_REMOVAL_DOCKER_IMAGE
    
    # Validate aggressiveness mode
    if aggressiveness_mode not in [1, 2, 3]:
        error_msg = f"Invalid aggressiveness mode: {aggressiveness_mode}. Must be 1, 2, or 3."
        logger.error(error_msg)
        return False, error_msg, output_file_info
    
    try:
        # Validate PDF file exists
        if not os.path.exists(pdf_file_path):
            error_msg = f"PDF file not found: {pdf_file_path}"
            logger.error(error_msg)
            return False, error_msg, output_file_info
        
        # Convert to absolute paths for Docker
        pdf_file_path = os.path.abspath(pdf_file_path)
        
        # Get output filename (add suffix to avoid replacing original)
        pdf_filename = os.path.basename(pdf_file_path)
        pdf_name_without_ext = os.path.splitext(pdf_filename)[0]
        output_filename = f"{pdf_name_without_ext}_watermark_removed_m{aggressiveness_mode}.pdf"
        
        # Output will be in same directory as input
        output_dir = os.path.dirname(pdf_file_path)
        output_file_path = os.path.join(output_dir, output_filename)
        
        logger.info(
            f"Watermark removal starting for doc_id={doc_id}, user_id={user_id}\n"
            f"  Input PDF path: {pdf_file_path}\n"
            f"  Output PDF path: {output_file_path}\n"
            f"  Aggressiveness mode: {aggressiveness_mode}\n"
            f"  Docker image: {docker_image}\n"
            f"  is_container_path: {is_container_path(output_dir)}\n"
            f"  WORKSPACE_PATH env: {os.getenv('WORKSPACE_PATH')}"
        )
        
        # Get the directory containing the PDF
        pdf_dir = os.path.dirname(pdf_file_path)
        
        # Construct Docker command
        docker_command = [
            "docker",
            "run",
            "--rm",
            "-v", f"{pdf_dir}:/workspace",
            docker_image,
            "-i", f"/workspace/{pdf_filename}",
            "-o", f"/workspace/{output_filename}",
            "-m", str(aggressiveness_mode)
        ]
        
        logger.info(f"Docker command: {' '.join(docker_command)}")
        
        # Execute Docker command
        try:
            result = subprocess.run(
                docker_command,
                timeout=DOCKER_EXTRACTION_TIMEOUT,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit
            )
            
            logger.info(f"Docker stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"Docker stderr: {result.stderr}")
            
            # Check if output file was created
            if os.path.exists(output_file_path):
                output_file_size = os.path.getsize(output_file_path)
                
                output_file_info = {
                    "filename": output_filename,
                    "path": output_file_path,
                    "size": output_file_size,
                    "status": "completed",
                    "aggressiveness_mode": aggressiveness_mode
                }
                
                success_msg = (
                    f"Watermark removal successful for doc_id={doc_id}. "
                    f"Output: {output_filename} ({output_file_size} bytes)"
                )
                logger.info(success_msg)
                return True, success_msg, output_file_info
            else:
                error_msg = f"Docker did not produce output file: {output_file_path}"
                logger.error(error_msg)
                logger.error(f"Docker exit code: {result.returncode}")
                return False, error_msg, output_file_info
        
        except subprocess.TimeoutExpired:
            error_msg = (
                f"Watermark removal timed out after {DOCKER_EXTRACTION_TIMEOUT} seconds "
                f"for doc_id={doc_id}"
            )
            logger.error(error_msg)
            return False, error_msg, output_file_info
        
        except Exception as e:
            error_msg = f"Docker execution error for doc_id={doc_id}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, output_file_info
    
    except Exception as e:
        error_msg = f"Unexpected error during watermark removal for doc_id={doc_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg, output_file_info
