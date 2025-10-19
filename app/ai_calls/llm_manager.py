"""
LLM Manager using LangChain Groq for structured receipt parsing
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from langchain_core.globals import set_llm_cache
from langchain_community.cache import InMemoryCache
from dotenv import load_dotenv
from app.schemas.schemas import ReceiptCreate, ItemCreate, ParsedReceiptData

# Load environment variables from .env file
load_dotenv()

# Enable caching to avoid repeated calls
set_llm_cache(InMemoryCache())


class LLMManager:
    """LLM Manager using LangChain Groq for structured receipt parsing."""
    
    def __init__(self):
        """Initialize LLM Manager with LangChain Groq client."""
        api_key = os.getenv("GROQ_API_KEY")
        try:
            # Initialize Groq LLM with updated approach
            self.llm = ChatGroq(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.2,
                api_key=api_key
            )
            print("✅ LangChain Groq client initialized successfully")
        except Exception as e:
            print(f"Warning: Groq client initialization failed: {e}")
            print("Note: Set GROQ_API_KEY environment variable to use Groq API")
            self.llm = None
    
    def parse_receipt_text(self, text: str) -> Dict[str, Any]:
        """Parse receipt text using LangChain Groq for structured extraction."""
        if not self.llm:
            # Fallback to simple parsing when Groq is not available
            print("⚠️ Groq not available, using simple fallback parsing...")
            return self._simple_fallback_parse(text)
            
        # LLM Prompt — Exactly like Colab script with clearer instructions
        prompt = f"""You are an expert in extracting structured data from unstructured text.
Given the extracted text from a store receipt, return a JSON with:
store_name, date, time, items (item_name, item_price), and total_amount.

IMPORTANT: Extract ONLY the store name (e.g., "WALMART", "TARGET", "COSTCO") - not addresses or other text.

Extract from this text:
{text}

JSON fields (EXACT field names required):
- store_name (ONLY the store name, max 50 characters)
- date
- time
- items (list of objects with EXACT field names: item_name, item_price)
- subtotal
- tax
- total
- payment_method
- cashier
- confidence_score (between 0.0 to 1.0)

CRITICAL REQUIREMENTS:
1. Use EXACT field names: item_name and item_price (not name and price)
2. For items, if specific names aren't clear, use descriptive names like "Item 1", "Item 2"
3. Calculate subtotal as sum of all item prices
4. Calculate total as subtotal + tax
5. Return ALL fields with proper values, not null"""

        try:
            # Call Groq Model
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse JSON Output
            try:
                # Clean the response content - extract JSON from markdown blocks
                content = response.content.strip()
                
                # Look for JSON block in markdown format
                if '```json' in content:
                    # Extract JSON from ```json ... ``` block
                    start = content.find('```json') + 7
                    end = content.find('```', start)
                    if end != -1:
                        content = content[start:end].strip()
                elif '```' in content:
                    # Extract JSON from ``` ... ``` block
                    start = content.find('```') + 3
                    end = content.find('```', start)
                    if end != -1:
                        content = content[start:end].strip()
                
                # Try to find JSON object in the content
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}')
                    if end != -1:
                        content = content[start:end + 1]
                
                structured_data = json.loads(content.strip())
                return structured_data
            except json.JSONDecodeError:
                print("⚠️ Model did not return valid JSON. Raw output:")
                print(response.content)
                print("Using fallback parsing...")
                return self._simple_fallback_parse(text)
            
        except Exception as e:
            print(f"⚠️ Groq API call failed: {e}, using fallback...")
            return self._simple_fallback_parse(text)
    
    def _simple_fallback_parse(self, text: str) -> Dict[str, Any]:
        """Simple fallback parsing when Groq is not available."""
        result = {
            "store_name": None,
            "date": None,
            "time": None,
            "items": [],
            "subtotal": None,
            "tax": None,
            "total": None,
            "payment_method": None,
            "cashier": None
        }
        
        # Extract store name - look for common store patterns
        lines = text.split('\n')
        for line in lines:
            line_upper = line.upper().strip()
            if 'SUPERCENTER' in line_upper:
                result["store_name"] = line_upper.replace('SUPERCENTER', '').strip()
                break
            elif 'STORE' in line_upper and len(line_upper) < 50:
                result["store_name"] = line_upper.replace('STORE', '').strip()
                break
        
        # Extract date and time using simple string operations
        for line in lines:
            line = line.strip()
            if '/' in line and len(line) == 10:  # Date format MM/DD/YYYY
                try:
                    # Validate it's a date
                    parts = line.split('/')
                    if len(parts) == 3 and all(part.isdigit() for part in parts):
                        result["date"] = line
                        break
                except:
                    continue
        
        for line in lines:
            line = line.strip()
            if ':' in line and len(line) == 5:  # Time format HH:MM
                try:
                    # Validate it's a time
                    parts = line.split(':')
                    if len(parts) == 2 and all(part.isdigit() for part in parts):
                        result["time"] = line
                        break
                except:
                    continue
        
        # Extract cashier
        for line in lines:
            if 'CASHIER:' in line.upper():
                result["cashier"] = line.split('CASHIER:')[1].strip()
                break
        
        # Extract items with prices - look for item patterns
        items = []
        for line in lines:
            line = line.strip()
            if '$' in line and len(line) > 5:
                # Check if this looks like an item line
                parts = line.split('$')
                if len(parts) == 2:
                    item_name = parts[0].strip()
                    price_str = parts[1].strip()
                    
                    # Skip if this looks like a total/subtotal/tax line
                    skip_keywords = ['SUBTOTAL', 'TAX', 'TOTAL', 'SAVED', 'ITEM', 'PRICE']
                    if not any(keyword in item_name.upper() for keyword in skip_keywords):
                        try:
                            item_price = float(price_str)
                            items.append({
                                "item_name": item_name,
                                "item_price": item_price
                            })
                        except ValueError:
                            continue
        
        result["items"] = items
        
        # Extract subtotal
        for line in lines:
            if 'SUBTOTAL' in line.upper() and '$' in line:
                try:
                    price_str = line.split('$')[1].strip()
                    result["subtotal"] = float(price_str)
                    break
                except ValueError:
                    continue
        
        # Extract tax
        for line in lines:
            if 'TAX' in line.upper() and '$' in line:
                try:
                    price_str = line.split('$')[1].strip()
                    result["tax"] = float(price_str)
                    break
                except ValueError:
                    continue
        
        # Extract total
        for line in lines:
            if 'TOTAL' in line.upper() and '$' in line and 'SUBTOTAL' not in line.upper():
                try:
                    price_str = line.split('$')[1].strip()
                    result["total"] = float(price_str)
                    break
                except ValueError:
                    continue
        
        # If we have items but no subtotal, calculate it
        if result["items"] and result["subtotal"] is None:
            result["subtotal"] = sum(item["item_price"] for item in result["items"])
        
        # If we have subtotal and tax but no total, calculate it
        if result["subtotal"] and result["tax"] and result["total"] is None:
            result["total"] = result["subtotal"] + result["tax"]
        
        # If we have items and tax but no subtotal, calculate it
        if result["items"] and result["tax"] and result["subtotal"] is None:
            result["subtotal"] = sum(item["item_price"] for item in result["items"])
            result["total"] = result["subtotal"] + result["tax"]
        
        # Extract payment method using simple string operations
        text_lower = text.lower()
        if "debit" in text_lower:
            result["payment_method"] = "debit"
        elif "credit card" in text_lower:
            result["payment_method"] = "credit"
        elif "cash" in text_lower:
            result["payment_method"] = "cash"
        elif "visa" in text_lower:
            result["payment_method"] = "visa"
        
        return result
    
    def calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted data."""
        score = 0.0
        
        # Helper function to safely convert price to float
        def safe_float(value):
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    cleaned = value.replace('$', '').replace(',', '').strip()
                    return float(cleaned)
                except ValueError:
                    return None
            return None
        
        # Store name (optional but important)
        if data.get('store_name'):
            score += 0.15
        
        # Date (optional)
        if data.get('date'):
            score += 0.15
        
        # Time (optional)
        if data.get('time'):
            score += 0.1
        
        # Amounts (subtotal, tax, total)
        subtotal = safe_float(data.get('subtotal'))
        if subtotal is not None and subtotal > 0:
            score += 0.2
        
        tax = safe_float(data.get('tax'))
        if tax is not None and tax >= 0:
            score += 0.15
        
        total = safe_float(data.get('total'))
        if total is not None and total > 0:
            score += 0.2
        
        # Payment method (optional)
        if data.get('payment_method'):
            score += 0.05
        
        # Items (important)
        if data.get('items') and len(data['items']) > 0:
            score += 0.2
        
        return min(score, 1.0)
    
    def validate_and_convert_to_receipt(self, json_data: Dict[str, Any]) -> ReceiptCreate:
        """Validate JSON data and convert to ReceiptCreate schema."""
        try:
            # Helper function to convert price strings to floats
            def convert_price(price_value):
                if price_value is None:
                    return None
                if isinstance(price_value, (int, float)):
                    return float(price_value)
                if isinstance(price_value, str):
                    # Remove dollar signs and convert to float
                    cleaned = price_value.replace('$', '').replace(',', '').strip()
                    try:
                        return float(cleaned)
                    except ValueError:
                        return None
                return None
            
            # Convert items to ItemCreate objects
            items = []
            for item_data in json_data.get('items', []):
                # Handle both item_name/item_price and name/price formats
                item_name = item_data.get('item_name') or item_data.get('name', 'Unknown Item')
                item_price = convert_price(item_data.get('item_price') or item_data.get('price'))
                
                items.append(ItemCreate(
                    item_name=item_name,
                    item_price=item_price
                ))
            
            # Clean and validate store name (truncate if too long)
            store_name = json_data.get('store_name', '')
            if store_name and len(store_name) > 100:
                store_name = store_name[:100].strip()
            
            # Create ReceiptCreate object (schema will handle date/time conversion)
            receipt = ReceiptCreate(
                store_name=store_name,
                date=json_data.get('date'),  # Schema will convert string to date
                time=json_data.get('time'),  # Schema will convert string to time
                subtotal=convert_price(json_data.get('subtotal')),
                tax=convert_price(json_data.get('tax')),
                total=convert_price(json_data.get('total')),
                payment_method=json_data.get('payment_method'),
                items=items
            )
            return receipt
        except Exception as e:
            raise ValueError(f"Error validating receipt data: {str(e)}")
    
    def process_receipt(self, text: str) -> Dict[str, Any]:
        """Process receipt text and return structured data with confidence score."""
        try:
            # Parse using LangChain Groq
            result = self.parse_receipt_text(text)
            
            # Add confidence score if parsing was successful
            if "error" not in result:
                confidence_score = self.calculate_confidence_score(result)
                result["confidence_score"] = confidence_score
            
            return result
            
        except Exception as e:
            return {
                "error": f"Receipt processing failed: {str(e)}",
                "confidence_score": 0.0
            }
    
    def process_with_fallback(self, text: str) -> Dict[str, Any]:
        """Alias for process_receipt to maintain compatibility."""
        return self.process_receipt(text)


# Global LLM manager instance
llm_manager = LLMManager()