from fastapi import FastAPI, HTTPException, Depends, Query, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv
from cachetools import TTLCache
import json

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Sheet2API",
    description="A RESTful API service that transforms Google Sheets and Excel Online spreadsheets into APIs",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# Cache configuration
cache = TTLCache(maxsize=100, ttl=300)  # Cache with 5 minutes TTL

# Google Sheets setup
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'

def get_credentials():
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE")
    if not creds_file:
        raise HTTPException(status_code=500, detail="Google credentials not configured")
    try:
        return ServiceAccountCredentials.from_json_keyfile_name(creds_file, SCOPES)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load credentials: {str(e)}"
        )

def get_sheet_service():
    try:
        credentials = get_credentials()
        return gspread.authorize(credentials)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize Google Sheets service: {str(e)}")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key

class SheetData(BaseModel):
    data: List[Dict[str, Any]]

def clean_worksheet_data(worksheet_obj):
    """
    Clean and validate worksheet data, handling empty cells in headers.
    """
    try:
        # Get all values including empty cells
        all_values = worksheet_obj.get_all_values()
        if not all_values:
            return []
        
        # Get headers (first row) and remove empty or whitespace-only cells
        headers = [h.strip() for h in all_values[0] if h.strip()]
        if not headers:
            return []
        
        # Process remaining rows
        records = []
        for row in all_values[1:]:
            # Trim row to match header length
            row = row[:len(headers)]
            # Pad row if it's shorter than headers
            row.extend([''] * (len(headers) - len(row)))
            # Create record dictionary with non-empty headers
            record = {headers[i]: row[i] for i in range(len(headers))}
            records.append(record)
        
        return records
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing worksheet data: {str(e)}"
        )

@app.get("/api/v1/sheets/{sheet_id}", response_model=SheetData)
async def get_sheet_data(
    sheet_id: str,
    worksheet: Optional[str] = None,
    limit: Optional[int] = Query(None, ge=1),
    offset: Optional[int] = Query(None, ge=0),
    sort: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve data from a Google Sheet with optional filtering and sorting.
    If worksheet is not provided, uses the first sheet.
    """
    # Extract query parameters excluding the known parameters
    filters = {}
    
    cache_key = f"{sheet_id}:{worksheet}:{limit}:{offset}:{sort}:{json.dumps(filters, sort_keys=True)}"
    
    if cache_key in cache:
        return {"data": cache[cache_key]}

    try:
        service = get_sheet_service()
        try:
            sheet = service.open_by_key(sheet_id)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Sheet not found. Please check if the sheet_id is correct and the service account has access to it. Error: {str(e)}"
            )
        
        try:
            if worksheet is None:
                # Get the first worksheet if none specified
                worksheet_obj = sheet.get_worksheet(0)
                if worksheet_obj is None:
                    raise HTTPException(
                        status_code=404,
                        detail="No worksheets found in the spreadsheet"
                    )
            else:
                # Get the specified worksheet
                worksheet_obj = sheet.worksheet(worksheet)
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Worksheet '{worksheet}' not found in the sheet. Error: {str(e)}"
            )
        
        try:
            # Get all records with cleaned data
            records = clean_worksheet_data(worksheet_obj)
            if not records:
                return {"data": [], "message": "The sheet exists but contains no valid data or headers"}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error reading records from worksheet: {str(e)}"
            )
        
        # Apply filters if any
        if filters:
            filtered_records = []
            for record in records:
                if all(str(record.get(k, "")).lower() == str(v).lower() for k, v in filters.items()):
                    filtered_records.append(record)
            records = filtered_records
        
        # Apply sorting
        if sort:
            field, direction = sort.split(":") if ":" in sort else (sort, "asc")
            reverse = direction.lower() == "desc"
            records = sorted(records, key=lambda x: str(x.get(field, "")), reverse=reverse)
        
        # Apply pagination
        if offset:
            records = records[offset:]
        if limit:
            records = records[:limit]
        
        cache[cache_key] = records
        return {"data": records}
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@app.get("/api/v1/sheets/{sheet_id}/search", response_model=SheetData)
async def search_sheet(
    sheet_id: str,
    worksheet: Optional[str] = None,
    q: str = Query(..., description="Search query"),
    fields: Optional[List[str]] = Query(None, description="Fields to search in"),
    api_key: str = Depends(verify_api_key)
):
    """
    Search for data in a Google Sheet.
    If worksheet is not provided, uses the first sheet.
    """
    try:
        service = get_sheet_service()
        sheet = service.open_by_key(sheet_id)
        
        try:
            if worksheet is None:
                # Get the first worksheet if none specified
                worksheet_obj = sheet.get_worksheet(0)
                if worksheet_obj is None:
                    raise HTTPException(
                        status_code=404,
                        detail="No worksheets found in the spreadsheet"
                    )
            else:
                # Get the specified worksheet
                worksheet_obj = sheet.worksheet(worksheet)
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Worksheet '{worksheet}' not found in the sheet. Error: {str(e)}"
            )
        
        # Get all records with cleaned data
        records = clean_worksheet_data(worksheet_obj)
        search_results = []
        
        q = q.lower()
        for record in records:
            if fields:
                # Search only in specified fields
                search_text = " ".join(str(record.get(field, "")).lower() for field in fields)
            else:
                # Search in all fields
                search_text = " ".join(str(v).lower() for v in record.values())
            
            if q in search_text:
                search_results.append(record)
        
        return {"data": search_results}
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching sheet: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 