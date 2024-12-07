from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
from typing import Dict, List
import json

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Road types to query
ROAD_TYPES = [
    "motorway", 
    "trunk", 
    "primary", 
    "secondary", 
    "tertiary", 
    "unclassified", 
    "residential"
]

@app.post("/api4/roads")
async def query_roads(request: Request):
    try:
        # Parse JSON request body
        body = await request.json()
        
        # Extract polygon coordinates
        polygon_coords = body.get('polygonCoords')
        
        # Validate inputs
        if not polygon_coords:
            raise HTTPException(status_code=400, detail="Missing polygon coordinates")

        # Prepare to store results
        road_results: Dict[str, List] = {}

        # Use httpx for concurrent requests
        async with httpx.AsyncClient() as client:
            # Create queries for all road types
            tasks = []
            for road_type in ROAD_TYPES:
                query = f"""
                [out:json];
                way["highway"="{road_type}"](poly:"{polygon_coords}");
                (._;>;);
                out body geom;
                """
                
                # Prepare request
                task = client.post(
                    'https://overpass-api.de/api/interpreter', 
                    content=query,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                tasks.append((road_type, task))

            # Send concurrent requests
            for road_type, task in tasks:
                response = await task
                
                # Log and handle errors
                if response.status_code != 200:
                    logger.error(f"Overpass API error for {road_type}: {response.text}")
                    road_results[road_type] = []
                    continue

                # Parse and store results
                road_data = response.json()
                road_results[road_type] = road_data.get('elements', [])

        return road_results
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Health check endpoint
@app.get("/")
async def health_check():
    return {"status": "healthy"}
