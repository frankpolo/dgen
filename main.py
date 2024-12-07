from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
from typing import Dict, List
import json
import asyncio

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

async def fetch_road_data(client, road_type, polygon_coords):
    try:
        # Split large polygons into chunks if necessary
        query = f"""
        [out:json][timeout:180];
        way["highway"="{road_type}"](poly:"{polygon_coords}");
        (._;>;);
        out body geom;
        """
        
        response = await client.post(
            'https://overpass-api.de/api/interpreter', 
            content=query,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=180.0  # 3-minute timeout
        )
        
        if response.status_code != 200:
            logger.error(f"Overpass API error for {road_type}: {response.text}")
            return []
        
        road_data = response.json()
        return road_data.get('elements', [])
    
    except httpx.RequestError as e:
        logger.error(f"Request error for {road_type}: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error for {road_type}: {str(e)}")
        return []

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
        
        # Trim and validate coordinate string
        polygon_coords = polygon_coords.strip()
        
        # Prepare to store results
        road_results: Dict[str, List] = {}
        
        # Use httpx for concurrent requests
        async with httpx.AsyncClient(timeout=200.0) as client:
            # Create concurrent tasks for road types
            tasks = [
                fetch_road_data(client, road_type, polygon_coords) 
                for road_type in ROAD_TYPES
            ]
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*[
                asyncio.create_task(fetch_road_data(client, road_type, polygon_coords)) 
                for road_type in ROAD_TYPES
            ])
            
            # Combine results
            for road_type, result in zip(ROAD_TYPES, results):
                road_results[road_type] = result
        
        return road_results
    
    except asyncio.TimeoutError:
        logger.error("Request timed out")
        raise HTTPException(status_code=504, detail="Request timed out")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Health check endpoint
@app.get("/")
async def health_check():
    return {"status": "healthy"}
