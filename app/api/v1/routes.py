"""
API routes for receipt management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.db.database import get_db
from app.models.models import Receipt
from app.schemas.schemas import (
    ReceiptCreate, ReceiptUpdate, ReceiptResponse, 
    ReceiptListResponse, AnalyticsResponse
)
from app.services.data_manager import data_manager
from app.services.services import ReceiptService
from app.parsers.ocr_parser import ocr_parser
from app.ai_calls.llm_manager import llm_manager

# Create router
router = APIRouter()


@router.post("/receipts/", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def create_receipt(receipt: ReceiptCreate, db: Session = Depends(get_db)):
    """Create a new receipt."""
    try:
        db_receipt = ReceiptService.create_receipt(db, receipt)
        return db_receipt
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/receipts/", response_model=ReceiptListResponse)
async def get_receipts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all receipts with pagination."""
    receipts = ReceiptService.get_receipts(db, skip, limit)
    total = ReceiptService.count_receipts(db)
    
    return ReceiptListResponse(
        receipts=receipts,
        total=total,
        page=skip // limit + 1,
        size=limit
    )


@router.get("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(receipt_id: int, db: Session = Depends(get_db)):
    """Get a specific receipt by ID."""
    receipt = ReceiptService.get_receipt(db, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@router.put("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt(
    receipt_id: int, 
    receipt: ReceiptUpdate, 
    db: Session = Depends(get_db)
):
    """Update a receipt."""
    db_receipt = ReceiptService.update_receipt(db, receipt_id, receipt)
    if not db_receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return db_receipt


@router.delete("/receipts/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_receipt(receipt_id: int, db: Session = Depends(get_db)):
    """Delete a receipt."""
    success = ReceiptService.delete_receipt(db, receipt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Receipt not found")


@router.get("/receipts/store/{store_name}", response_model=ReceiptListResponse)
async def get_receipts_by_store(
    store_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get receipts by store name."""
    receipts = ReceiptService.get_receipts_by_store(db, store_name, skip, limit)
    total = ReceiptService.count_receipts_by_store(db, store_name)
    
    return ReceiptListResponse(
        receipts=receipts,
        total=total,
        page=skip // limit + 1,
        size=limit
    )


@router.get("/receipts/date-range/", response_model=ReceiptListResponse)
async def get_receipts_by_date_range(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get receipts within a date range."""
    receipts = ReceiptService.get_receipts_by_date_range(db, start_date, end_date, skip, limit)
    total = ReceiptService.count_receipts_by_date_range(db, start_date, end_date)
    
    return ReceiptListResponse(
        receipts=receipts,
        total=total,
        page=skip // limit + 1,
        size=limit
    )


@router.get("/analytics/", response_model=AnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """Get analytics data."""
    return ReceiptService.get_analytics(db)


@router.post("/receipts/upload/", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process receipt document (image, PDF, or DOCX) using advanced OCR and AI.
    
    Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF, PDF, DOCX
    """
    try:
        # Step 1: Extract text using OCR
        ocr_result = await ocr_parser.parse_document(file)
        
        if not ocr_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"OCR extraction failed: {ocr_result.get('error', 'Unknown error')}"
            )
        
        # Step 2: Save raw data (OCR result)
        file_extension = file.filename.split('.')[-1].lower() if file.filename else 'unknown'
        raw_filename = data_manager.save_raw_data({
            "filename": file.filename,
            "file_type": file_extension,
            "ocr_text": ocr_result["processed_text"],
            "ocr_confidence": ocr_result.get("confidence", 0.0)
        }, file_extension)
        
        # Step 3: Process text with LLM to extract structured data
        json_data = llm_manager.process_with_fallback(ocr_result["processed_text"])
        
        if "error" in json_data:
            raise HTTPException(
                status_code=400,
                detail=f"Text processing failed: {json_data['error']}"
            )
        
        # Step 4: Validate and convert to ReceiptCreate schema
        try:
            receipt_data = llm_manager.validate_and_convert_to_receipt(json_data)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Data validation failed: {str(e)}"
            )
        
        # Step 5: Save to database
        db_receipt = ReceiptService.create_receipt(db, receipt_data)
        
        # Step 6: Save curated data with database ID
        curated_filename = data_manager.save_curated_data(
            json_data, 
            db_receipt.id, 
            raw_filename
        )
        
        # Step 7: Return response with metadata
        response_data = {
            "id": db_receipt.id,
            "store_name": db_receipt.store_name,
            "date": db_receipt.date,
            "time": db_receipt.time,
            "subtotal": float(db_receipt.subtotal) if db_receipt.subtotal else None,
            "tax": float(db_receipt.tax) if db_receipt.tax else None,
            "total": float(db_receipt.total) if db_receipt.total else None,
            "payment_method": db_receipt.payment_method,
            "items": [
                {
                    "id": item.id,
                    "item_name": item.item_name,
                    "item_price": float(item.item_price)
                }
                for item in db_receipt.items
            ],
            "curated_filename": curated_filename,
            "raw_filename": raw_filename
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error processing document: {str(e)}"
        )


@router.post("/receipts/save/", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def save_receipt_to_database(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Save structured receipt data to database and curated data folder.
    """
    try:
        receipt_data = request.get("receipt_data", request)  # Handle both formats
        raw_filename = request.get("raw_filename", "unknown")
        
        # Validate and convert to ReceiptCreate schema
        try:
            receipt_create = llm_manager.validate_and_convert_to_receipt(receipt_data)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Data validation failed: {str(e)}"
            )
        
        # Save to database
        db_receipt = ReceiptService.create_receipt(db, receipt_create)
        
        # Save curated data with database ID
        curated_filename = data_manager.save_curated_data(
            receipt_data, 
            db_receipt.id, 
            raw_filename
        )
        
        # Add metadata to response
        response_data = {
            "id": db_receipt.id,
            "store_name": db_receipt.store_name,
            "date": db_receipt.date,
            "time": db_receipt.time,
            "subtotal": float(db_receipt.subtotal) if db_receipt.subtotal else None,
            "tax": float(db_receipt.tax) if db_receipt.tax else None,
            "total": float(db_receipt.total) if db_receipt.total else None,
            "payment_method": db_receipt.payment_method,
            "items": [
                {
                    "id": item.id,
                    "item_name": item.item_name,
                    "item_price": float(item.item_price)
                }
                for item in db_receipt.items
            ],
            "curated_filename": curated_filename,
            "raw_filename": raw_filename
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving receipt to database: {str(e)}"
        )


@router.post("/receipts/process-text/", response_model=dict)
async def process_text_directly(request: dict):
    """
    Process unstructured text directly using LLM.
    Returns structured JSON data without saving to database.
    """
    try:
        text = request.get("text", "")
        if not text:
            return {
                "success": False,
                "error": "No text provided",
                "structured_data": None,
                "confidence_score": 0.0
            }
        
        # Save raw data first
        raw_filename = data_manager.save_raw_data({"text": text}, "text")
        
        # Process text directly with LLM (no OCR needed)
        json_data = llm_manager.process_with_fallback(text)
        
        # Validate the structured data
        if "error" in json_data:
            return {
                "success": False,
                "error": json_data["error"],
                "structured_data": None,
                "confidence_score": 0.0
            }
        
        return {
            "success": True,
            "structured_data": json_data,
            "confidence_score": json_data.get("confidence_score", 0.0),
            "message": "Text processed successfully with LLM",
            "raw_filename": raw_filename
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "structured_data": None,
            "confidence_score": 0.0
        }


@router.get("/data/stats/")
async def get_data_stats():
    """Get statistics about stored raw and curated data."""
    return data_manager.get_data_stats()


@router.get("/data/raw/")
async def list_raw_data():
    """List all raw data files."""
    return {"raw_files": data_manager.list_raw_data()}


@router.get("/data/curated/")
async def list_curated_data():
    """List all curated data files."""
    return {"curated_files": data_manager.list_curated_data()}


@router.get("/data/raw/{filename}")
async def get_raw_data(filename: str):
    """Get raw data by filename."""
    data = data_manager.get_raw_data(filename)
    if not data:
        raise HTTPException(status_code=404, detail="Raw data file not found")
    return data


@router.get("/data/curated/{filename}")
async def get_curated_data(filename: str):
    """Get curated data by filename."""
    data = data_manager.get_curated_data(filename)
    if not data:
        raise HTTPException(status_code=404, detail="Curated data file not found")
    return data
