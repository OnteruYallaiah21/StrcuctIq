// JavaScript for Receipt Intelligence Upload Page

class ReceiptProcessor {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000/api/v1';
        this.currentReceiptData = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // File upload elements
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const textInput = document.getElementById('textInput');
        const processTextBtn = document.getElementById('processTextBtn');

        // Upload area events
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));

        // File input change
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Text processing
        processTextBtn.addEventListener('click', this.processText.bind(this));

        // Action buttons
        document.getElementById('saveReceiptBtn').addEventListener('click', this.saveReceipt.bind(this));
        document.getElementById('processAnotherBtn').addEventListener('click', this.resetForm.bind(this));
        document.getElementById('retryBtn').addEventListener('click', this.resetForm.bind(this));
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    async processFile(file) {
        // Validate file type
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf'];
        if (!allowedTypes.includes(file.type)) {
            this.showToast('Please upload a PNG, JPG, or PDF file.', 'error');
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            this.showToast('File size must be less than 10MB.', 'error');
            return;
        }

        this.showProcessingSection();
        this.updateProgress(10, 'Uploading file...');

        try {
            const formData = new FormData();
            formData.append('file', file);

            this.updateProgress(30, 'Processing with OCR...');

            const response = await fetch(`${this.apiBaseUrl}/receipts/upload/`, {
                method: 'POST',
                body: formData
            });

            this.updateProgress(70, 'Extracting structured data...');

            if (response.ok) {
                const receiptData = await response.json();
                this.updateProgress(100, 'Processing complete!');
                
                setTimeout(() => {
                    this.hideProcessingSection();
                    this.displayResults(receiptData);
                    this.showToast('Receipt processed successfully!', 'success');
                    this.resetFileInput(); // Reset file input after successful processing
                }, 500);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }
        } catch (error) {
            console.error('Error processing file:', error);
            this.hideProcessingSection();
            
            // Check if it's a Tesseract error and provide helpful message
            if (error.message.includes('Tesseract') || error.message.includes('OCR')) {
                this.showError('OCR Error: ' + error.message + '<br><br>💡 <strong>Tip:</strong> You can still use the text input field below to process receipt text manually.');
            } else {
                this.showError(error.message);
            }
            
            this.showToast('Error processing receipt: ' + error.message, 'error');
            this.resetFileInput(); // Reset file input after error
        }
    }

    async processText() {
        const text = document.getElementById('textInput').value.trim();
        
        if (!text) {
            this.showToast('Please enter some receipt text.', 'error');
            return;
        }

        this.showProcessingSection();
        this.updateProgress(20, 'Processing text...');

        try {
            this.updateProgress(50, 'Analyzing with AI...');

            const response = await fetch(`${this.apiBaseUrl}/receipts/process-text/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });

            this.updateProgress(80, 'Structuring data...');

            if (response.ok) {
                const result = await response.json();
                
                if (result.success) {
                    this.updateProgress(100, 'Processing complete!');
                    
                    setTimeout(() => {
                        this.hideProcessingSection();
                        this.currentRawFilename = result.raw_filename; // Store raw filename
                        this.displayResults(result.structured_data);
                        this.showToast('Text processed successfully!', 'success');
                    }, 500);
                } else {
                    throw new Error(result.error || 'Text processing failed');
                }
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Text processing failed');
            }
        } catch (error) {
            console.error('Error processing text:', error);
            this.hideProcessingSection();
            this.showError(error.message);
            this.showToast('Error processing text: ' + error.message, 'error');
        }
    }

    async saveReceipt() {
        if (!this.currentReceiptData) {
            this.showToast('No receipt data to save.', 'error');
            return;
        }

        try {
            // Prepare request with raw filename if available
            const requestData = {
                receipt_data: this.currentReceiptData,
                raw_filename: this.currentRawFilename || 'unknown'
            };

            const response = await fetch(`${this.apiBaseUrl}/receipts/save/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            if (response.ok) {
                const savedReceipt = await response.json();
                this.showToast(`Receipt saved successfully! ID: ${savedReceipt.id}`, 'success');
                
                // Show file information
                if (savedReceipt.curated_filename) {
                    this.showToast(`Curated data saved: ${savedReceipt.curated_filename}`, 'info');
                }
                if (savedReceipt.raw_filename) {
                    this.showToast(`Raw data saved: ${savedReceipt.raw_filename}`, 'info');
                }
                
                // Update the save button
                const saveBtn = document.getElementById('saveReceiptBtn');
                saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved to Database';
                saveBtn.disabled = true;
                saveBtn.classList.remove('btn-success');
                saveBtn.classList.add('btn-secondary');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Save failed');
            }
        } catch (error) {
            console.error('Error saving receipt:', error);
            this.showToast('Error saving receipt: ' + error.message, 'error');
        }
    }

    displayResults(data) {
        this.currentReceiptData = data;
        
        // Update confidence score
        const confidence = Math.round((data.confidence_score || 0) * 100);
        document.getElementById('scoreValue').textContent = `${confidence}%`;
        
        // Update receipt details
        document.getElementById('storeName').textContent = data.store_name || '-';
        document.getElementById('receiptDate').textContent = data.date || '-';
        document.getElementById('receiptTime').textContent = data.time || '-';
        document.getElementById('paymentMethod').textContent = data.payment_method || '-';
        
        // Update amounts
        document.getElementById('subtotal').textContent = data.subtotal || '$0.00';
        document.getElementById('tax').textContent = data.tax || '$0.00';
        document.getElementById('total').textContent = data.total || '$0.00';
        
        // Update items
        this.displayItems(data.items || []);
        
        // Display complete JSON
        this.displayJSON(data);
        
        // Show results section
        document.getElementById('resultsSection').style.display = 'block';
        
        // Reset save button
        const saveBtn = document.getElementById('saveReceiptBtn');
        saveBtn.innerHTML = '<i class="fas fa-save"></i> Save to Database';
        saveBtn.disabled = false;
        saveBtn.classList.remove('btn-secondary');
        saveBtn.classList.add('btn-success');
    }

    displayItems(items) {
        const itemsList = document.getElementById('itemsList');
        itemsList.innerHTML = '';
        
        if (items.length === 0) {
            itemsList.innerHTML = '<div class="item-row"><span class="item-name">No items found</span></div>';
            return;
        }
        
        items.forEach(item => {
            const itemRow = document.createElement('div');
            itemRow.className = 'item-row';
            // Handle both item_name/item_price and name/price formats
            const itemName = item.item_name || item.name || 'Unknown Item';
            const itemPrice = item.item_price || item.price || '0.00';
            itemRow.innerHTML = `
                <span class="item-name">${itemName}</span>
                <span class="item-price">$${itemPrice}</span>
            `;
            itemsList.appendChild(itemRow);
        });
    }

    displayJSON(data) {
        const jsonOutput = document.getElementById('jsonOutput');
        if (jsonOutput) {
            jsonOutput.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        }
    }

    showProcessingSection() {
        document.getElementById('processingSection').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
    }

    hideProcessingSection() {
        document.getElementById('processingSection').style.display = 'none';
    }

    updateProgress(percent, status) {
        document.getElementById('progressFill').style.width = `${percent}%`;
        document.getElementById('processingStatus').textContent = status;
    }

    showError(message) {
        let errorMessage = message;
        
        // Provide helpful messages for common OCR errors
        if (message.includes('Tesseract OCR is not installed')) {
            errorMessage = `OCR Error: Tesseract is not installed on the server.
            
To fix this:
1. Install Tesseract OCR on your system
2. macOS: brew install tesseract
3. Ubuntu: sudo apt-get install tesseract-ocr
4. Windows: Download from GitHub

For now, you can use the text input field below to manually enter receipt data.`;
        } else if (message.includes('No text could be extracted')) {
            errorMessage = `OCR Error: No text could be extracted from the image.
            
This might happen if:
- The image is blurry or low quality
- The text is too small or unclear
- The image contains only graphics without text

Try using a clearer image or use the text input field below.`;
        } else if (message.includes('Unsupported file format')) {
            errorMessage = `File Format Error: The uploaded file format is not supported.
            
Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF, PDF, DOCX

Please upload a file in one of these formats or use the text input field below.`;
        }
        
        document.getElementById('errorMessage').innerHTML = errorMessage.replace(/\n/g, '<br>');
        document.getElementById('errorSection').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'none';
    }

    resetForm() {
        // Hide all sections
        document.getElementById('processingSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        // Clear form
        document.getElementById('fileInput').value = '';
        document.getElementById('textInput').value = '';
        
        // Reset upload area
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.classList.remove('dragover');
        
        // Clear current data
        this.currentReceiptData = null;
        
        this.showToast('Form reset. Ready for new receipt!', 'info');
    }

    resetFileInput() {
        // Reset file input to allow uploading the same file again
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.value = '';
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'fas fa-check-circle' : 
                    type === 'error' ? 'fas fa-exclamation-circle' : 
                    'fas fa-info-circle';
        
        toast.innerHTML = `
            <i class="${icon}"></i>
            <span>${message}</span>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ReceiptProcessor();
    
    // Show welcome message
    setTimeout(() => {
        const processor = new ReceiptProcessor();
        processor.showToast('Welcome to Receipt Intelligence! Upload a receipt to get started.', 'info');
    }, 1000);
});
