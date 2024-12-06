from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from pydantic import BaseModel

app = FastAPI()

# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OverpassQuery(BaseModel):
    query: str

# Basic rate limiting dictionary (simple in-memory approach)
request_count = {}
MAX_REQUESTS_PER_MINUTE = 50

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    # Initialize count for this IP if not exists
    if client_ip not in request_count:
        request_count[client_ip] = 1
    else:
        request_count[client_ip] += 1
    
    # Check if IP has exceeded rate limit
    if request_count[client_ip] > MAX_REQUESTS_PER_MINUTE:
        return JSONResponse(
            status_code=429, 
            content={"detail": "Too many requests. Please try again later."}
        )
    
    response = await call_next(request)
    return response

@app.post("/api/roads")
async def query_overpass(query_data: OverpassQuery):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://overpass-api.de/api/interpreter', 
                data=query_data.query,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Check if request was successful
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail="Error querying Overpass API"
                )
            
            return response.json()
    
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Optional health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
