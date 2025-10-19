# Struct-Recipt-Intilligent

A production-grade FastAPI service for managing receipt data with intelligent OCR processing and AI analysis capabilities using LangChain and Groq.

## 🔄 Processing Flow

```
Unstructured OCR Text (Images/PDFs)
          │
          ▼
   OCR Parser (pytesseract/PyMuPDF)
   ──────────────► Raw Text
          │
          ▼
   LLM Manager (Groq AI Processing)
   ──────────────► Structured JSON
          │
          ▼
   Database Manager (SQLAlchemy)
   ──────────────► PostgreSQL Database
          │
          ▼
   Analytics & Insights
   ──────────────► Human-readable Reports
```

## 🏗️ Project Structure

```
Struct-Recipt-Intilligent/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   └── v1/                   # API version 1
│   │       ├── __init__.py
│   │       └── routes.py         # Receipt endpoints
│   ├── core/                     # Core configuration
│   │   ├── __init__.py
│   │   └── config.py             # App settings
│   ├── db/                       # Database configuration
│   │   ├── __init__.py
│   │   └── database.py           # Database session management
│   ├── models/                   # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── models.py             # Receipt and Item models
│   ├── schemas/                  # Pydantic schemas
│   │   ├── __init__.py
│   │   └── schemas.py            # Request/Response models
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── services.py           # Receipt service layer
│   │   └── data_manager.py       # Data storage management
│   ├── parsers/                  # OCR and text processing
│   │   ├── __init__.py
│   │   └── ocr_parser.py         # OCR text extraction
│   └── ai_calls/                 # AI and LLM processing
│       ├── __init__.py
│       └── llm_manager.py        # LLM text processing
├── Testing-Data/                 # Test data folder
│   ├── walmart bill.png         # Sample Walmart receipt image
│   └── [Additional test images] # More sample receipt images
├── data/                         # Generated data storage
│   ├── raw_data/                # Raw OCR text files
│   └── curated_data/            # Processed structured data
├── static/                       # Static web files
│   ├── index.html               # Main upload page
│   ├── css/style.css            # Styling
│   └── js/app.js                # JavaScript functionality
├── requirements.txt              # Python dependencies
├── env.example                   # Environment variables template
├── start_server.py              # Server startup script
├── test_*.py                    # Various test scripts
└── README.md                    # This file
```

## 🚀 Quick Start

### 1. Create and Activate Virtual Environment

   ```bash
# Create virtual environment
   python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### 2. Install Dependencies

   ```bash
   pip install -r requirements.txt
   ```

**Note**: For OCR functionality, you also need to install Tesseract OCR:
- **macOS**: `brew install tesseract`
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

**Note**: For LangChain and Groq functionality, you need a Groq API key:
- Sign up at [Groq Console](https://console.groq.com/)
- Get your API key and add it to your `.env` file

### 3. Setup Environment

```bash
cp env.example .env
# Edit .env with your database configuration
```

### 4. Start the Server

**Option A: Using the startup script (Recommended)**
```bash
python start_server.py
```

**Option B: Using uvicorn directly**
   ```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **Web Interface**: http://localhost:8000 (HTML upload page)
- **API**: http://localhost:8000/api/v1/
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Testing-Data Folder

The `Testing-Data/` folder contains sample receipt images for testing the OCR functionality:

### Available Test Images

#### 1. Walmart Receipt (`walmart bill.png`)
- **Description**: Sample Walmart Supercenter receipt
- **Format**: PNG image
- **Content**: Complete receipt with store info, items, prices, tax, and totals
- **Use Case**: Test OCR text extraction and structured data parsing
- **Expected Results**: 
  - Store name: "WALMART" or "WALMART SUPERCENTER"
  - Items with prices
  - Subtotal, tax, and total amounts
  - Payment method and transaction details

### How to Use Test Images

1. **Web Interface Testing:**
   ```bash
   # Start the server
   python start_server.py
   
   # Open browser: http://localhost:8000
   # Drag and drop Testing-Data/walmart bill.png onto upload area
   # Or click "browse files" and select the image
   ```

2. **API Testing:**
   ```bash
   # Test image upload via API
   curl -X POST "http://localhost:8000/api/v1/receipts/upload/" \
     -F "file=@Testing-Data/walmart bill.png"
   ```

3. **Python Script Testing:**
   ```bash
   # Test OCR integration
   python test_ocr_integration.py
   
   # Test Colab integration
   python test_colab_integration.py
   ```

### Adding More Test Images

To add more test images to the `Testing-Data/` folder:

1. **Supported Formats:**
   - PNG, JPG, JPEG (recommended for receipts)
   - PDF documents
   - DOCX documents

2. **Image Requirements:**
   - Clear, readable text
   - Good contrast between text and background
   - Minimum resolution: 300x300 pixels
   - Maximum file size: 20MB

3. **Naming Convention:**
   ```
   Testing-Data/
   ├── walmart bill.png
   ├── target_receipt.jpg
   ├── costco_sample.png
   ├── grocery_store_receipt.pdf
   └── restaurant_bill.jpg
   ```

4. **Testing New Images:**
   ```bash
   # Test with new image
   curl -X POST "http://localhost:8000/api/v1/receipts/upload/" \
     -F "file=@Testing-Data/your_new_image.png"
   ```

### Expected OCR Results

When processing images from the Testing-Data folder, you should expect:

- **Text Extraction**: Clear OCR text output
- **Structured Data**: Parsed JSON with store name, items, prices
- **Confidence Score**: High confidence (>0.8) for clear images
- **Database Save**: Successful saving to database

### Troubleshooting Test Images

**Problem**: Image not uploading
```bash
# Check if file exists
ls -la Testing-Data/walmart\ bill.png

# Check file permissions
chmod 644 Testing-Data/walmart\ bill.png
```

**Problem**: OCR not extracting text
```bash
# Test Tesseract installation
python test_tesseract.py

# Check image format
file Testing-Data/walmart\ bill.png
```

**Problem**: Poor OCR results
```bash
# Ensure image has good contrast
# Try different image formats (PNG usually works best)
# Check if image is too small or blurry
```

## 🧪 Testing the Application

### Test Data Examples

#### 1. Text Input Examples

**Simple Receipt Text:**
```
i went costco bought maybe 4.5 and then 2.30 i think tax 1.3 used debit card probably
```

**Structured Receipt Text:**
```
WALMART SUPERCENTER
1234 MAIN STREET
ANYTOWN, USA 12345
(555) 123-4567
ST# 01234 OP# 001 TR# 56789
07/12/2024 14:32
ITEM PRICE
MILK 2L $3.49
BREAD WHOLE WHEAT $2.29
EGGS 12CT $4.10
SUBTOTAL $9.88
TAX 8.0% $0.79
TOTAL $10.67
CREDIT CARD
**** **** **** 1234
CASHIER: JOHN D.
```

**Casual Receipt Text:**
```
went to target got milk 3.4 bread 2.2 and small tax 0.7 not sure total tho
```

**Multiple Items Text:**
```
purchased at walmart some veggies 5.6 meat 7.8 tax 2.1 payd by cash maybe
```

#### 2. Image Upload Examples

**Test Images Available in Testing-Data Folder:**
- `Testing-Data/walmart bill.png` - Sample Walmart receipt image

**Supported Image Formats:**
- PNG, JPG, JPEG, GIF, BMP, TIFF (recommended for receipts)
- PDF documents
- DOCX documents

**How to Test with Images:**
1. **Web Interface:**
   - Drag and drop `Testing-Data/walmart bill.png` onto the upload area
   - Or click "browse files" and select the image
   - Review the OCR extracted text and structured data

2. **API Testing:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/receipts/upload/" \
     -F "file=@Testing-Data/walmart bill.png"
   ```

3. **Expected Results:**
   - OCR text extraction from the image
   - Structured data with store name, items, prices, totals
   - Confidence score based on extraction quality

### Testing Methods

#### Method 1: Web Interface Testing

1. **Start the server:**
   ```bash
   python start_server.py
   ```

2. **Open browser:** http://localhost:8000

3. **Test Text Processing:**
   - Paste any of the text examples above into the text area
   - Click "Process Text"
   - Review the extracted structured data
   - Click "Save to Database" to store the results

4. **Test Image Upload:**
   - Drag and drop `Testing-Data/walmart bill.png` onto the upload area
   - Or click "browse files" and select the image
   - Review the OCR extracted text and structured data
   - Save to database if satisfied

#### Method 2: API Testing

**Test Text Processing API:**
```bash
curl -X POST "http://localhost:8000/api/v1/receipts/process-text/" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "i went costco bought maybe 4.5 and then 2.30 i think tax 1.3 used debit card probably"
  }'
```

**Test Image Upload API:**
```bash
curl -X POST "http://localhost:8000/api/v1/receipts/upload/" \
  -F "file=@Testing-Data/walmart bill.png"
```

**Test Receipt Creation:**
```bash
curl -X POST "http://localhost:8000/api/v1/receipts/" \
  -H "Content-Type: application/json" \
  -d '{
    "store_name": "Walmart Supercenter",
    "date": "2024-07-12",
    "time": "14:32",
    "subtotal": 9.88,
    "tax": 0.79,
    "total": 10.67,
    "payment_method": "Credit Card",
    "items": [
      {"item_name": "Milk 2L", "item_price": 3.49},
      {"item_name": "Bread Whole Wheat", "item_price": 2.29},
      {"item_name": "Eggs 12ct", "item_price": 4.10}
    ]
  }'
```

#### Method 3: Python Script Testing

**Run the test scripts:**
```bash
# Test basic API functionality
python test_llm_simple.py

# Test OCR integration
python test_ocr_integration.py

# Test Colab integration
python test_colab_integration.py

# Test Tesseract installation
python test_tesseract.py

# Test HTML interface
python test_html_interface.py
```

### Expected Results

#### Text Processing Results

**Input:** `i went costco bought maybe 4.5 and then 2.30 i think tax 1.3 used debit card probably`

**Expected Output:**
```json
{
  "store_name": "COSTCO",
  "date": null,
  "time": null,
  "items": [
    {
      "item_name": "Item 1",
      "item_price": 4.5
    },
    {
      "item_name": "Item 2", 
      "item_price": 2.3
    }
  ],
  "subtotal": 6.8,
  "tax": 1.3,
  "total": 8.1,
  "payment_method": "debit card",
  "cashier": null,
  "confidence_score": 0.95
}
```

#### Image Processing Results

**Input:** `Testing-Data/walmart bill.png`

**Expected Output:**
- OCR extracted text from the image
- Structured data with store name, items, prices, totals
- Confidence score based on extraction quality

## 🔧 Troubleshooting

### Virtual Environment Issues

**Problem**: `python: command not found` or `pip: command not found`
```bash
# Make sure you're using Python 3
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

**Problem**: Virtual environment not activating
```bash
# Check if venv directory exists
ls -la venv/

# If not, recreate it
rm -rf venv
python -m venv venv
source venv/bin/activate
```

### Server Startup Issues

**Problem**: `ModuleNotFoundError` when starting server
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Verify packages are installed
pip list | grep fastapi
pip list | grep uvicorn

# Reinstall if needed
pip install -r requirements.txt
```

**Problem**: Port 8000 already in use
```bash
# Kill existing process
pkill -f uvicorn

# Wait a moment, then try again
python start_server.py

# Or use a different port
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Problem**: Database connection failed
```bash
# The app will run without database - this is normal
# Check the terminal output for "⚠️ Database connection failed"
# The app will still work for text processing
```

### OCR Issues

**Problem**: Tesseract not found
```bash
# Install Tesseract
# macOS:
brew install tesseract

# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# Windows: Download from GitHub
```

**Problem**: Image processing fails
```bash
# Check if image file exists and is readable
ls -la Testing-Data/walmart\ bill.png

# Test Tesseract directly
python test_tesseract.py
```

### LLM Issues

**Problem**: Groq API errors
```bash
# Check if GROQ_API_KEY is set in .env file
cat .env | grep GROQ_API_KEY

# Test Groq connection
python test_llm_simple.py
```

### Common Commands

```bash
# Complete setup from scratch
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
python start_server.py

# Quick restart
pkill -f uvicorn
source venv/bin/activate
python start_server.py
```

## 📊 Database Schema

### Receipts Table
```sql
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    store_name VARCHAR(100),
    date DATE,
    time TIME,
    subtotal NUMERIC(10,2),
    tax NUMERIC(10,2),
    total NUMERIC(10,2),
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Items Table
```sql
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    receipt_id INTEGER REFERENCES receipts(id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    item_price NUMERIC(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔌 API Endpoints

### Receipt Management
- `POST /api/v1/receipts/` - Create a new receipt
- `GET /api/v1/receipts/` - Get all receipts (paginated)
- `GET /api/v1/receipts/{id}` - Get specific receipt
- `PUT /api/v1/receipts/{id}` - Update receipt
- `DELETE /api/v1/receipts/{id}` - Delete receipt

### Filtering & Search
- `GET /api/v1/receipts/store/{store_name}` - Get receipts by store
- `GET /api/v1/receipts/date-range/` - Get receipts by date range

### OCR & File Upload
- `POST /api/v1/receipts/upload/` - Upload and process receipt document (image/PDF)
- `POST /api/v1/receipts/process-text/` - Process unstructured text directly

### Database Operations
- `POST /api/v1/receipts/save/` - Save processed receipt to database

## 🌐 Web Interface

The application includes a modern web interface for easy receipt processing:

### Features
- **Drag & Drop Upload**: Simply drag receipt files (PNG, JPG, PDF) onto the upload area
- **Text Input**: Paste unstructured receipt text directly
- **Real-time Processing**: See processing status with progress indicators
- **Structured Display**: View extracted data in a clean, organized format
- **Confidence Scoring**: See how confident the AI is about the extraction
- **Database Integration**: Save processed receipts directly to the database
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### Usage
1. Start the server: `python start_server.py`
2. Open your browser: http://localhost:8000
3. Upload a receipt file or paste text
4. Review the extracted data
5. Save to database if satisfied

## 📝 Example Usage

### Create a Receipt
```bash
curl -X POST "http://localhost:8000/api/v1/receipts/" \
  -H "Content-Type: application/json" \
  -d '{
    "store_name": "Walmart Supercenter",
    "date": "2024-07-12",
    "time": "14:32",
    "subtotal": 9.88,
    "tax": 0.79,
    "total": 10.67,
    "payment_method": "Credit Card",
    "items": [
      {"item_name": "Milk 2L", "item_price": 3.49},
      {"item_name": "Bread Whole Wheat", "item_price": 2.29},
      {"item_name": "Eggs 12ct", "item_price": 4.10}
    ]
  }'
```

### Get Analytics
```bash
curl "http://localhost:8000/api/v1/analytics/"
```

## 🛠️ Development

### Running in Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables
   ```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/structured_data_db

# App Settings
APP_NAME=Struct-Recipt-Intilligent API
APP_VERSION=1.0.0
DEBUG=false

# API Settings
API_V1_PREFIX=/api/v1
ALLOWED_ORIGINS=["*"]

# Groq API Configuration
GROQ_API_KEY=your-groq-api-key-here
```

## 🧪 Testing

Run the test suite:
```bash
python test_llm_simple.py
```

The test scripts will:
1. Test LLM processing with sample text
2. Test OCR integration with images
3. Test API endpoints
4. Test database operations
5. Test web interface functionality

## 📦 Dependencies

- **FastAPI**: Modern web framework for building APIs
- **SQLAlchemy**: Python SQL toolkit and ORM
- **PostgreSQL**: Database
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server implementation
- **LangChain**: Framework for building LLM applications
- **Groq**: High-performance LLM inference platform
- **Tesseract**: OCR engine for text extraction
- **PyMuPDF**: PDF processing library
- **OpenCV**: Image processing library
- **Pillow**: Python Imaging Library

## 🔧 Configuration

The application uses a clean separation of concerns:

- **Models**: SQLAlchemy database models
- **Schemas**: Pydantic request/response validation
- **Services**: Business logic layer
- **Routes**: API endpoint definitions
- **Core**: Application configuration and settings
- **Parsers**: OCR and text processing
- **AI Calls**: LLM processing with Groq

## 📈 Features

- ✅ RESTful API design
- ✅ Automatic API documentation
- ✅ Data validation with Pydantic
- ✅ Database ORM with SQLAlchemy
- ✅ Pagination support
- ✅ Analytics endpoints
- ✅ Error handling
- ✅ CORS support
- ✅ Clean project structure
- ✅ Production-ready configuration
- ✅ OCR text extraction (Tesseract)
- ✅ PDF processing (PyMuPDF)
- ✅ LangChain integration
- ✅ Groq LLM processing
- ✅ Structured output parsing
- ✅ Fallback regex parsing
- ✅ File upload support
- ✅ Confidence scoring
- ✅ Modern web interface
- ✅ Drag & drop functionality
- ✅ Real-time processing status
- ✅ Responsive design
- ✅ Test data examples
- ✅ Comprehensive documentation

## 🎯 Quick Test Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Server started (`python start_server.py`)
- [ ] Web interface accessible (http://localhost:8000)
- [ ] Text processing works (paste test text)
- [ ] Image upload works (upload `Testing-Data/walmart bill.png`)
- [ ] Database save works (click "Save to Database")
- [ ] API endpoints respond (check http://localhost:8000/docs)

## 📞 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Run the test scripts to identify the problem
3. Check the server logs for error messages
4. Verify all dependencies are installed correctly
5. Ensure Tesseract OCR is installed for image processing
6. Verify Groq API key is set for LLM processing

## 🚀 Production Deployment

For production deployment:

1. Set up a PostgreSQL database
2. Configure environment variables
3. Use a production ASGI server like Gunicorn
4. Set up proper logging and monitoring
5. Configure reverse proxy (nginx)
6. Set up SSL certificates
7. Configure backup strategies

---

**Happy Receipt Processing! 🧾✨**