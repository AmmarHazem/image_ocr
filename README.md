# PDF and Image OCR Service

A Flask-based REST API service that performs Optical Character Recognition (OCR) on PDFs and images, with specialized features for processing invoices and medical documents.

## Features

- PDF to text conversion with OCR
- Image to text conversion
- Batch number extraction from medical vial images
- Line item extraction from invoices
- Multi-threaded PDF processing
- Confidence scoring for OCR results

## Prerequisites

- Python 3.x
- Tesseract OCR engine
- Required Python packages (see Installation)

## Installation

1. Install Tesseract OCR engine:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # macOS
   brew install tesseract
   
   # Windows
   # Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

2. Install Python dependencies:
   ```bash
   pip install pytesseract pdf2image Pillow flask requests langchain-openai
   ```

## API Endpoints

### 1. Extract Batch Number from Image

```http
GET /extract-batch-number-from-image?image_url={url}
```

Extracts batch number from an image of a medical vial.

**Query Parameters:**
- `image_url`: URL of the image to process

**Response:**
```json
{
    "results": {
        "batch_number": "ABC123"
    }
}
```

### 2. Extract Text from Image

```http
GET /extract-text-from-image?image_url={url}
```

Performs OCR on an image and returns extracted text.

**Query Parameters:**
- `image_url`: URL of the image to process

**Response:**
```json
{
    "results": "Extracted text content..."
}
```

### 3. Extract Text from PDF

```http
GET /extract-text-from-pdf?pdf_url={url}
```

Converts PDF to images and performs OCR to extract text.

**Query Parameters:**
- `pdf_url`: URL of the PDF to process

**Response:**
```json
{
    "results": [
        {
            "page": 1,
            "text": "Extracted text from page 1...",
            "confidence": 95.5
        },
        {
            "page": 2,
            "text": "Extracted text from page 2...",
            "confidence": 93.2
        }
    ]
}
```

### 4. Extract Line Items from Invoice

```http
GET /extract-line-items-from-fusion-invoice?pdf_url={url}
```

Extracts structured line item data from invoice PDFs.

**Query Parameters:**
- `pdf_url`: URL of the invoice PDF to process

**Response:**
```json
{
    "results": [
        {
            "item": "Product Name",
            "expiry_date": "2024-12-31",
            "lot_no": "LOT123",
            "quantity": 5
        }
    ]
}
```

### 5. Status Check

```http
GET /status
```

Checks if the service is running.

**Response:**
```json
{
    "status": "ok",
    "count": 1
}
```

## Additional Information

For more details about the service, please refer to the documentation.

## Contact

If you have any questions or need further assistance, please contact us at:

- Email: [contact@example.com](mailto:contact@example.com)
- Phone: +1 (555) 123-4567

Thank you for using our service!