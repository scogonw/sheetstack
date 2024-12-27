# SheetStack 📊

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com)

Transform Google Sheets into a complete full-stack solution instantly. SheetStack provides a simple way to use Google Sheets as your application backend with features like filtering, sorting, and full-text search.

## 🌟 Features

- 🔄 **Complete Backend Solution**: Transform any Google Sheet into a full-featured REST API
- 🔍 **Advanced Querying**:
  - Filtering by column values
  - Sorting (ascending/descending)
  - Pagination support
  - Full-text search across all or specific columns
- 🔒 **Security**:
  - API key authentication
  - Support for private Google Sheets
  - CORS support
- ⚡ **Performance**:
  - Built-in caching
  - Efficient data processing
  - Clean data handling

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- A Google Cloud Project with Google Sheets API enabled
- Google Service Account credentials

### Installation

1. Clone the repository:
```bash
git clone https://github.com/scogonw/sheetstack.git
cd sheetstack
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Sheets API:
   1. Go to [Google Cloud Console](https://console.cloud.google.com)
   2. Create a new project or select an existing one
   3. Enable the Google Sheets API
   4. Create a Service Account:
      - Go to "IAM & Admin" > "Service Accounts"
      - Click "Create Service Account"
      - Download the JSON credentials file
   5. Save the credentials file in your project directory

4. Configure environment:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Update `.env` with your settings:
     ```
     API_KEY=your_api_key_here
     GOOGLE_CREDENTIALS_FILE=path_to_your_credentials.json
     ```

### Running the Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Endpoints

#### 1. Get Sheet Data
```http
GET /api/v1/sheets/{sheet_id}
```

Query Parameters:
- `worksheet` (optional): Sheet name (defaults to first sheet)
- `limit`: Number of records to return
- `offset`: Number of records to skip
- `sort`: Sort by field (format: "field:asc" or "field:desc")
- Any column name can be used as a filter parameter

#### 2. Search Sheet Data
```http
GET /api/v1/sheets/{sheet_id}/search
```

Query Parameters:
- `worksheet` (optional): Sheet name (defaults to first sheet)
- `q`: Search query
- `fields`: Specific fields to search in (optional)

#### 3. Health Check
```http
GET /health
```

### Authentication

Include your API key in request headers:
```http
X-API-Key: your_api_key_here
```

## 🔐 Working with Private Sheets

1. Get your service account email from credentials.json
2. Share your Google Sheet with the service account email
3. Use the sheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
   ```

## 📝 Example Usage

### Basic Data Retrieval
```bash
curl -H "X-API-Key: your_api_key" \
     "http://localhost:8000/api/v1/sheets/your_sheet_id"
```

### Filtered Data
```bash
curl -H "X-API-Key: your_api_key" \
     "http://localhost:8000/api/v1/sheets/your_sheet_id?status=active"
```

### Sorted Data
```bash
curl -H "X-API-Key: your_api_key" \
     "http://localhost:8000/api/v1/sheets/your_sheet_id?sort=date:desc"
```

### Search
```bash
curl -H "X-API-Key: your_api_key" \
     "http://localhost:8000/api/v1/sheets/your_sheet_id/search?q=searchterm"
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ Show Your Support

Give a ⭐️ if this project helped you!

## 📧 Contact

ScogonW - [@scogonw](https://twitter.com/scogonw)

Project Link: [https://github.com/scogonw/sheetstack](https://github.com/scogonw/sheetstack) 