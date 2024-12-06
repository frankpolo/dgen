from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import json
import logging


app = FastAPI()
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/roads")
async def query_overpass(request: Request):
    try:
        # Log the raw request body for debugging
        body_raw = await request.body()
        logger.debug(f"Raw request body: {body_raw}")

        # Try to parse the body as JSON
        try:
            body = await request.json()
            logger.debug(f"Parsed JSON body: {body}")
        except Exception as json_error:
            logger.error(f"JSON parsing error: {json_error}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(json_error)}")

        # Validate query
        query = body.get('query')
        if not query:
            logger.error("No query found in request body")
            raise HTTPException(status_code=400, detail="Query is required")

        # Log the query for debugging
        logger.debug(f"Extracted query: {query}")

        # Make Overpass API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://overpass-api.de/api/interpreter', 
                content=query,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Log response details
            logger.debug(f"Overpass API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Overpass API error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Overpass API error: {response.text}"
                )
            
            return response.json()
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Add a simple health check endpoint
@app.get("/")
async def health_check():
    return {"status": "healthy"}
