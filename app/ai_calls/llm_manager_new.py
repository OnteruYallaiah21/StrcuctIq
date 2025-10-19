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


class LLMManager:
    """LLM Manager using direct Groq API calls for structured receipt parsing."""
    
    def __init__(self):
        """Initialize LLM Manager with Groq client."""
        api_key = os.getenv("GROQ_API_KEY", "your-groq-api-key-here")
        self.client = Groq(api_key=api_key)
        self.model_name = "mixtral-8x7b-32768"  # Using Mixtral model
    
    def parse_receipt_text(self, text: str) -> Dict[str, Any]:
        """Send unstructured text to Groq model for structured extraction."""
        prompt = f"""
        You are a structured data extractor.

        Extract all relevant purchase information from the text below.
        Return only valid JSON (no explanations, no markdown).

        Required fields:
        store_name, date, time, items (list of {{item_name, item_price}}),
        subtotal, tax, total, payment_method.

        If any field is missing, use null.

        Text:
        {text}
        """

        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=0.1
            )

            content = response.choices[0].message["content"].strip()

            # Parse JSON safely
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                print("⚠️ LLM returned invalid JSON. Attempting cleanup...")
                data = self._safe_json_parse(content)

            return data
            
        except Exception as e:
            return {"error": f"Groq API call failed: {str(e)}"}
    
    def _safe_json_parse(self, text: str) -> Dict[str, Any]:
        """Cleanup for malformed JSON (fallback)."""
        cleaned = re.sub(r"[^{}\[\]0-9A-Za-z.,:\"_\s-]", "", text)
        try:
            return json.loads(cleaned)
        except Exception:
            return {"error": "Could not parse output."}
    
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
        
        # Amounts (subtotal, tax, total)
        if data.get('subtotal') is not None and data['subtotal'] > 0:
            score += 0.2
        if data.get('tax') is not None and data['tax'] >= 0:
            score += 0.15
        if data.get('total') is not None and data['total'] > 0:
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
    
    def process_with_fallback(self, text: str) -> Dict[str, Any]:
        """Process text using direct Groq API call."""
        try:
            # Use direct Groq API call
            result = self.parse_receipt_text(text)
            
            # Add confidence score
            if "error" not in result:
                confidence_score = self.calculate_confidence_score(result)
                result["confidence_score"] = confidence_score
            
            return result
            
        except Exception as e:
            return {
                "error": f"Text processing failed: {str(e)}",
                "confidence_score": 0.0
            }


# Global LLM manager instance
llm_manager = LLMManager()
