"""
Pydantic schemas for request and response models
"""

from pydantic import BaseModel, Field, validator, field_validator, BeforeValidator
from typing import List, Optional, Dict, Any, Union, Annotated
from datetime import datetime, date, time


class ItemCreate(BaseModel):
    """Schema for creating an item."""
    item_name: str = Field(..., min_length=1, max_length=255)
    item_price: float = Field(..., gt=0)
    
    @validator('item_price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Item price must be greater than 0')
        return v


class ItemResponse(BaseModel):
    """Schema for item response."""
    id: int
    item_name: str
    item_price: float
    
    class Config:
        from_attributes = True


class ReceiptCreate(BaseModel):
    """Schema for creating a receipt."""
    store_name: Optional[str] = Field(None, max_length=100)
    date: Optional[str] = None  # Store as string, convert in service layer
    time: Optional[str] = None  # Store as string, convert in service layer
    subtotal: Optional[float] = Field(None, ge=0)
    tax: Optional[float] = Field(None, ge=0)
    total: Optional[float] = Field(None, ge=0)
    payment_method: Optional[str] = Field(None, max_length=50)
    items: List[ItemCreate] = Field(default_factory=list)
    
    @validator('total')
    def validate_total(cls, v, values):
        if v is not None and v < 0:
            raise ValueError('Total must be non-negative')
        return v


class ReceiptUpdate(BaseModel):
    """Schema for updating a receipt."""
    store_name: Optional[str] = Field(None, max_length=100)
    date: Optional[date] = None
    time: Optional[time] = None
    subtotal: Optional[float] = Field(None, ge=0)
    tax: Optional[float] = Field(None, ge=0)
    total: Optional[float] = Field(None, ge=0)
    payment_method: Optional[str] = Field(None, max_length=50)
    items: Optional[List[ItemCreate]] = None


class ReceiptResponse(BaseModel):
    """Schema for receipt response."""
    id: int
    store_name: Optional[str]
    date: Optional[date]
    time: Optional[time]
    subtotal: Optional[float]
    tax: Optional[float]
    total: Optional[float]
    payment_method: Optional[str]
    items: List[ItemResponse] = []
    
    class Config:
        from_attributes = True


class ReceiptListResponse(BaseModel):
    """Schema for receipt list response."""
    receipts: List[ReceiptResponse]
    total: int
    page: int
    size: int


class AnalyticsResponse(BaseModel):
    """Schema for analytics response."""
    total_receipts: int
    total_amount_spent: float
    average_receipt_amount: float
    top_stores: List[Dict[str, Any]]
    date_range: Dict[str, Any]


class ParsedReceiptData(BaseModel):
    """Schema for parsed receipt data from LLM."""
    store_name: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    payment_method: Optional[str] = None
    confidence_score: Optional[float] = None


class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str
    status_code: int
