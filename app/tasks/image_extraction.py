"""
Image extraction tasks for async processing
"""
from celery import current_task
from celery.exceptions import SoftTimeLimitExceeded
from app.celery_config import celery_app
from app.db.mongodb import get_documents_collection, get_images_collection
from app.utils.file_storage import figure_extraction_hook
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, name="tasks.extract_images")
def extract_images_from_document(self, doc_id: str, user_id: str, pdf_path: str):
    """
    Extract images from PDF document asynchronously
    
    This task:
    1. Updates document status to 'processing'
    2. Calls extraction hook (your existing code)
    3. Updates MongoDB with results
    4. Retries on failure (up to 3 times)
    
    Args:
        doc_id: MongoDB document ID
        user_id: User who uploaded document
        pdf_path: Full path to PDF file
        
    Returns:
        Dict with extraction results
        
    Raises:
        Retries automatically with exponential backoff on failure
    """
    documents_col = get_documents_collection()
    
    try:
        logger.info(f"Starting image extraction for doc_id={doc_id}")
        
        # Update status to processing
        documents_col.update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "extraction_status": "processing",
                    "extraction_started_at": datetime.utcnow(),
                    "extraction_retry_count": self.request.retries
                }
            }
        )
        
        # Run extraction using existing hook
        extracted_count, extraction_errors, extracted_files = figure_extraction_hook(
            doc_id=doc_id,
            user_id=user_id,
            pdf_file_path=pdf_path
        )
        
        # Determine final status
        if extraction_errors and extracted_count > 0:
            extraction_status = "completed_with_errors"
        elif extraction_errors and extracted_count == 0:
            extraction_status = "failed"
        else:
            extraction_status = "completed"
        
        logger.info(
            f"Extraction completed for doc_id={doc_id}: "
            f"extracted={extracted_count}, errors={len(extraction_errors)}"
        )
        
        # Store individual image records in images collection
        images_col = get_images_collection()
        if extracted_files:
            for image_file in extracted_files:
                image_doc = {
                    "user_id": user_id,
                    "filename": image_file['filename'],
                    "file_path": image_file['path'],
                    "file_size": image_file['size'],
                    "source_type": "extracted",
                    "document_id": doc_id,
                    "uploaded_date": datetime.utcnow()
                }
                images_col.insert_one(image_doc)
        
        # Update with final results
        documents_col.update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "extraction_status": extraction_status,
                    "extracted_image_count": extracted_count,
                    "extracted_images": extracted_files,  # Store detailed file info
                    "extraction_errors": extraction_errors,
                    "extraction_completed_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "doc_id": doc_id,
            "status": "success",
            "extracted_count": extracted_count,
            "errors": extraction_errors,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"Task timeout for doc_id={doc_id}")
        documents_col.update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "extraction_status": "failed",
                    "extraction_errors": ["Task execution timeout"]
                }
            }
        )
        raise
        
    except Exception as exc:
        logger.error(f"Extraction error for doc_id={doc_id}: {str(exc)}", exc_info=True)
        
        # Retry with exponential backoff
        countdown = 60 * (2 ** self.request.retries)
        logger.info(f"Retrying in {countdown} seconds (attempt {self.request.retries + 1}/3)")
        
        raise self.retry(exc=exc, countdown=countdown)
