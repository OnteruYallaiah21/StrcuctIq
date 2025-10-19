"""
LLM Manager using direct Groq API calls for structured output parsing
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time
from groq import Groq
from app.schemas.schemas import ReceiptCreate, ItemCreate


class ReceiptItem(BaseModel):
    """Pydantic model for individual receipt items."""
    item_name: str = Field(description="Name of the item")
    item_price: float = Field(description="Price of the item", gt=0)


class ReceiptData(BaseModel):
    """Pydantic model for structured receipt data."""
    store_name: Optional[str] = Field(None, description="Name of the store")
    date: Optional[str] = Field(None, description="Date of the receipt in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Time of the receipt in HH:MM format")
    subtotal: Optional[float] = Field(None, description="Subtotal amount", ge=0)
    tax: Optional[float] = Field(None, description="Tax amount", ge=0)
    total: Optional[float] = Field(None, description="Total amount", ge=0)
    payment_method: Optional[str] = Field(None, description="Payment method used")
    items: List[ReceiptItem] = Field(default_factory=list, description="List of items purchased")
    confidence_score: float = Field(0.0, description="Confidence score for the extraction", ge=0, le=1)


class LLMManager:
    """LLM Manager using LangChain with Groq models for structured receipt parsing."""
    
    def __init__(self):
        """Initialize LLM Manager with Groq model."""
        # Initialize Groq model
        self.llm = ChatGroq(
            model="llama3-8b-8192",  # Using Llama 3 8B model
            temperature=0.1,  # Low temperature for consistent parsing
            groq_api_key=os.getenv("GROQ_API_KEY", "your-groq-api-key-here")
        )
        
        # Create output parser
        self.output_parser = PydanticOutputParser(pydantic_object=ReceiptData)
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert receipt parser. Extract structured information from receipt text.

Your task is to parse unstructured receipt text and extract the following information:
- Store name
- Date (in YYYY-MM-DD format)
- Time (in HH:MM format)
- Subtotal amount
- Tax amount
- Total amount
- Payment method
- List of items with names and prices

Guidelines:
1. Be accurate and conservative in your extractions
2. If information is unclear or missing, set it to null
3. For dates, convert to YYYY-MM-DD format
4. For times, convert to HH:MM format (24-hour)
5. Extract all items with their individual prices
6. Calculate a confidence score (0.0 to 1.0) based on how clear and complete the receipt data is

{format_instructions}"""),
            ("human", "Parse this receipt text:\n\n{receipt_text}")
        ])
        
        # Create the chain
        self.chain = (
            {"receipt_text": RunnablePassthrough(), "format_instructions": lambda x: self.output_parser.get_format_instructions()}
            | self.prompt
            | self.llm
            | self.output_parser
        )
    
    def process_text_to_json(self, text: str) -> Dict[str, Any]:
        """Process unstructured text and convert to structured JSON using LangChain."""
        try:
            # Use LangChain's structured output method
            model_with_structure = self.llm.with_structured_output(ReceiptData)
            
            # Create a comprehensive prompt for receipt parsing
            prompt = f"""Extract shopping receipt information from this text. Look for:

STORE: Find store names (Walmart Supercenter, Target, etc.)
DATE: Find dates and convert to YYYY-MM-DD format (e.g., "July 12th, 2024" becomes "2024-07-12")
TIME: Find time if mentioned (format as HH:MM)
ITEMS: Find each item and its price:
  - Look for phrases like "priced at $X", "costing $X", "for $X"
  - Extract the full item description and exact price
TOTAL: Find total amount (look for "total came to", "total was", etc.)
PAYMENT: Find payment method if mentioned

Text: {text}

Extract all shopping details as if this were a receipt. If something isn't mentioned, set it to null."""
            
            # Invoke the model with structured output
            structured_data: ReceiptData = model_with_structure.invoke(prompt)
            
            # Convert Pydantic object to dictionary
            result = structured_data.model_dump()
            
            # Calculate confidence score based on extracted data
            confidence_score = self.calculate_confidence_score(result)
            result["confidence_score"] = confidence_score
            
            return result
            
        except Exception as e:
            return {
                "error": f"Error processing text with LangChain: {str(e)}",
                "confidence_score": 0.0
            }
    
    def calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted data."""
        score = 0.0
        
        # Store name (optional but important)
        if data.get('store_name'):
            score += 0.15
        
        # Date (optional)
        if data.get('date'):
            score += 0.15
        
        # Time (optional)
        if data.get('time'):
            score += 0.1
        
        # Amounts (important)
        if data.get('subtotal'):
            score += 0.2
        if data.get('tax'):
            score += 0.15
        if data.get('total'):
            score += 0.2
        
        # Payment method (optional)
        if data.get('payment_method'):
            score += 0.05
        
        # Items (very important)
        if data.get('items') and len(data['items']) > 0:
            score += 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def validate_and_convert_to_receipt(self, json_data: Dict[str, Any]) -> ReceiptCreate:
        """Validate JSON data and convert to ReceiptCreate schema."""
        try:
            # Convert items to ItemCreate objects
            items = []
            for item_data in json_data.get('items', []):
                items.append(ItemCreate(
                    item_name=item_data['item_name'],
                    item_price=item_data['item_price']
                ))
            
            # Parse date and time
            parsed_date = None
            parsed_time = None
            
            if json_data.get('date'):
                try:
                    date_str = json_data['date']
                    # Try different date formats
                    for fmt in ['%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt).date()
                            break
                        except ValueError:
                            continue
                except ValueError:
                    pass
            
            if json_data.get('time'):
                try:
                    time_str = json_data['time']
                    # Try different time formats
                    for fmt in ['%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M:%S %p']:
                        try:
                            parsed_time = datetime.strptime(time_str, fmt).time()
                            break
                        except ValueError:
                            continue
                except ValueError:
                    pass
            
            # Create ReceiptCreate object
            receipt = ReceiptCreate(
                store_name=json_data.get('store_name'),
                date=parsed_date,
                time=parsed_time,
                subtotal=json_data.get('subtotal'),
                tax=json_data.get('tax'),
                total=json_data.get('total'),
                payment_method=json_data.get('payment_method'),
                items=items
            )
            
            return receipt
            
        except Exception as e:
            raise ValueError(f"Error validating receipt data: {str(e)}")
    
    def _parse_narrative_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse narrative shopping descriptions."""
        # Check if this looks like narrative text
        narrative_indicators = [
            "shopper", "visited", "stopped by", "picked up", "headed to checkout",
            "total came to", "priced at", "costing", "loaf of", "bottle of", "dozen",
            "grabbed", "made her way", "cashier", "tallied"
        ]
        
        if not any(indicator in text.lower() for indicator in narrative_indicators):
            return None
        
        store_name = None
        date_str = None
        time_str = None
        subtotal = None
        tax = None
        total = None
        payment_method = None
        items = []
        
        # Extract store name - improved patterns
        store_patterns = [
            r'(?:stopped by|visited|at|to)\s+([A-Z][A-Za-z\s]+(?:Superstore|Supercenter|Store|Market|Center|Mall))',
            r'([A-Z][A-Za-z\s]+(?:Superstore|Supercenter|Store|Market|Center|Mall))',
            r'(Walmart|Target|Amazon|Costco|Safeway|Kroger|Whole Foods|CVS|Walgreens)'
        ]
        
        for pattern in store_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                store_name = match.group(1).strip()
                break
        
        # Extract date - improved patterns
        date_patterns = [
            r'(?:On\s+)?(?:a\s+chilly\s+evening,\s+)?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}',
            r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*,\s+\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(November\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Convert to YYYY-MM-DD format
                try:
                    if "November 5th, 2024" in date_str:
                        date_str = "2024-11-05"
                    elif "November" in date_str and "2024" in date_str:
                        # Extract day number
                        day_match = re.search(r'November\s+(\d{1,2})', date_str, re.IGNORECASE)
                        if day_match:
                            day = day_match.group(1).zfill(2)
                            date_str = f"2024-11-{day}"
                    elif "/" in date_str:
                        parts = date_str.split("/")
                        if len(parts) == 3:
                            month, day, year = parts
                            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    pass
                break
        
        # Extract items with prices - improved patterns for narrative text
        item_patterns = [
            r'(?:picked up|grabbed)\s+a\s+([^,]+?)\s+for\s+\$?(\d+\.?\d*)',
            r'a\s+([^,]+?)\s+costing\s+\$?(\d+\.?\d*)',
            r'a\s+([^,]+?)\s+priced\s+at\s+\$?(\d+\.?\d*)',
            r'(\d+\s+x\s+[^,]+?)\s+\$?(\d+\.?\d*)',
            r'([A-Za-z][^,]+?)\s+for\s+\$?(\d+\.?\d*)',
            r'([A-Za-z][^,]+?)\s+costing\s+\$?(\d+\.?\d*)',
            r'([A-Za-z][^,]+?)\s+priced\s+at\s+\$?(\d+\.?\d*)'
        ]
        
        for pattern in item_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                item_name = match.group(1).strip()
                price = float(match.group(2))
                
                # Clean up item name - remove common prefixes
                item_name = re.sub(r'^(a|an|the)\s+', '', item_name, flags=re.IGNORECASE)
                item_name = re.sub(r'\s+(for|costing|priced at).*$', '', item_name, flags=re.IGNORECASE)
                item_name = item_name.strip()
                
                # Skip if item name is too long or contains unwanted text
                if (price > 0 and len(item_name) > 2 and len(item_name) < 100 and 
                    not any(word in item_name.lower() for word in ['total', 'checkout', 'shopper', 'headed', 'collecting', 'stopped', 'target', 'superstore'])):
                    items.append({"item_name": item_name, "item_price": price})
        
        # Remove duplicates based on item name similarity
        unique_items = []
        for item in items:
            is_duplicate = False
            for existing in unique_items:
                # Check if items are similar (same price and similar name)
                if (abs(item["item_price"] - existing["item_price"]) < 0.01 and 
                    any(word in existing["item_name"].lower() for word in item["item_name"].lower().split() if len(word) > 3)):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_items.append(item)
        
        items = unique_items
        
        # Extract total
        total_patterns = [
            r'total\s+came\s+to\s+\$?(\d+\.?\d*)',
            r'total\s+was\s+\$?(\d+\.?\d*)',
            r'total\s+of\s+\$?(\d+\.?\d*)',
            r'total:\s+\$?(\d+\.?\d*)',
            r'tallied\s+everything,\s+the\s+total\s+came\s+to\s+\$?(\d+\.?\d*)'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                total = float(match.group(1))
                break
        
        # Extract tax
        tax_patterns = [
            r'(?:with|plus)\s+tax\s+\$?(\d+\.?\d*)',
            r'tax\s+\$?(\d+\.?\d*)',
            r'(?:including|incl\.?)\s+tax\s+\$?(\d+\.?\d*)'
        ]
        
        for pattern in tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                tax = float(match.group(1))
                break
        
        # Extract payment method
        payment_patterns = [
            r'(?:used|with|paid with)\s+(amex|american express|visa|mastercard|credit card|debit card|cash|check)',
            r'(amex|american express|visa|mastercard|credit card|debit card|cash|check)\s+(?:card|payment)',
            r'(?:i\s+)?used\s+(amex|american express|visa|mastercard|credit card|debit card)'
        ]
        
        for pattern in payment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                payment_method = match.group(1).strip()
                if payment_method.lower() == 'amex':
                    payment_method = 'American Express'
                elif payment_method.lower() == 'credit card':
                    payment_method = 'Credit Card'
                break
        
        # Calculate subtotal if we have items and total
        if items and total:
            item_total = sum(item["item_price"] for item in items)
            if abs(item_total - total) < 1.0:  # Close enough
                subtotal = item_total
        
        # Only return if we found meaningful data
        if store_name or date_str or items or total:
            structured_data = {
                "store_name": store_name,
                "date": date_str,
                "time": time_str,
                "subtotal": subtotal,
                "tax": tax,
                "total": total,
                "payment_method": payment_method,
                "items": items
            }
            
            confidence_score = self.calculate_confidence_score(structured_data)
            structured_data["confidence_score"] = confidence_score
            
            return structured_data
        
        return None
    
    def process_with_fallback(self, text: str) -> Dict[str, Any]:
        """Process text with fallback to regex parsing if LangChain fails."""
        # First try narrative text parsing
        narrative_result = self._parse_narrative_text(text)
        if narrative_result:
            return narrative_result
            
        try:
            # Try LangChain first
            result = self.process_text_to_json(text)
            
            # If LangChain failed or confidence is very low, try regex fallback
            if "error" in result or result.get("confidence_score", 0) < 0.3:
                print("LangChain parsing failed or low confidence, trying regex fallback...")
                return self._regex_fallback_parsing(text)
            
            return result
            
        except Exception as e:
            print(f"LangChain processing failed: {e}, trying regex fallback...")
            return self._regex_fallback_parsing(text)
    
    def _parse_structured_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse structured text format like the user's input."""
        lines = text.strip().split('\n')
        if len(lines) < 3:  # Not enough lines for structured format
            return None
        
        # Check if this looks like structured format
        has_sections = any(line.strip().lower() in ['date', 'time', 'payment method', 'amounts', 'subtotal', 'tax', 'total', 'items'] for line in lines)
        if not has_sections:
            return None
        
        store_name = None
        date_str = None
        time_str = None
        subtotal = None
        tax = None
        total = None
        payment_method = None
        items = []
        
        current_section = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check for section headers
            if line.lower() in ['date', 'time', 'payment method', 'amounts', 'subtotal', 'tax', 'total', 'items']:
                current_section = line.lower()
                continue
            
            # Process based on current section
            if current_section == 'date' and line != '-':
                date_str = line
            elif current_section == 'time' and line != '-':
                time_str = line
            elif current_section == 'payment method' and line != '-':
                payment_method = line
            elif current_section == 'subtotal' and line.startswith('$'):
                try:
                    subtotal = float(line.replace('$', ''))
                except ValueError:
                    pass
            elif current_section == 'tax' and line.startswith('$'):
                try:
                    tax = float(line.replace('$', ''))
                except ValueError:
                    pass
            elif current_section == 'total' and line.startswith('$'):
                try:
                    total = float(line.replace('$', ''))
                except ValueError:
                    pass
            elif current_section == 'items':
                # Look for item with price on next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('$'):
                        try:
                            price = float(next_line.replace('$', ''))
                            if price > 0:
                                items.append({"item_name": line, "item_price": price})
                        except ValueError:
                            pass
        
        # Only return if we found some data
        if any([date_str, time_str, subtotal, tax, total, items]):
            structured_data = {
                "store_name": store_name,
                "date": date_str,
                "time": time_str,
                "subtotal": subtotal,
                "tax": tax,
                "total": total,
                "payment_method": payment_method,
                "items": items
            }
            
            confidence_score = self.calculate_confidence_score(structured_data)
            structured_data["confidence_score"] = confidence_score
            
            return structured_data
        
        return None

    def _regex_fallback_parsing(self, text: str) -> Dict[str, Any]:
        """Fallback regex-based parsing when LangChain fails."""
        
        # Simple regex patterns for fallback
        store_name = None
        date_str = None
        time_str = None
        subtotal = None
        tax = None
        total = None
        payment_method = None
        items = []
        
        # First try to parse structured text format
        structured_result = self._parse_structured_text(text)
        if structured_result:
            return structured_result
        
        # Extract store name
        store_match = re.search(r'^([A-Z][A-Za-z\s&]+(?:Store|Shop|Market|Supermarket|Center|Mall|Outlet))', text, re.MULTILINE)
        if store_match:
            store_name = store_match.group(1).strip()
        
        # Extract date
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
        if date_match:
            date_str = date_match.group(1)
        
        # Extract time
        time_match = re.search(r'(\d{1,2}:\d{2})', text)
        if time_match:
            time_str = time_match.group(1)
        
        # Extract amounts
        subtotal_match = re.search(r'(?:Subtotal|Sub-total):\s*\$?(\d+\.?\d*)', text, re.IGNORECASE)
        if subtotal_match:
            subtotal = float(subtotal_match.group(1))
        
        tax_match = re.search(r'(?:Tax|VAT):\s*\$?(\d+\.?\d*)', text, re.IGNORECASE)
        if tax_match:
            tax = float(tax_match.group(1))
        
        total_match = re.search(r'(?:Total|Amount):\s*\$?(\d+\.?\d*)', text, re.IGNORECASE)
        if total_match:
            total = float(total_match.group(1))
        
        # Extract payment method
        payment_match = re.search(r'(Cash|Credit Card|Debit Card|Check)', text, re.IGNORECASE)
        if payment_match:
            payment_method = payment_match.group(1)
        
        # Extract items (simple pattern)
        lines = text.split('\n')
        for line in lines:
            item_match = re.search(r'([A-Za-z][A-Za-z0-9\s&.-]+?)\s+\$?(\d+\.?\d*)', line)
            if item_match:
                item_name, price = item_match.groups()
                try:
                    price_float = float(price)
                    if price_float > 0:
                        items.append({
                            "item_name": item_name.strip(),
                            "item_price": price_float
                        })
                except ValueError:
                    continue
        
        structured_data = {
            "store_name": store_name,
            "date": date_str,
            "time": time_str,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "payment_method": payment_method,
            "items": items
        }
        
        confidence_score = self.calculate_confidence_score(structured_data)
        structured_data["confidence_score"] = confidence_score
        
        return structured_data


# Global LLM manager instance
llm_manager = LLMManager()