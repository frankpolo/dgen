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
        # Log the full request body for debugging
        body = await request.json()
        logger.debug(f"Received request body: {body}")
        
        # Extract polygon coordinates
        polygon_coords = body.get('polygonCoords')
        
        # More detailed input validation
        if not polygon_coords or not isinstance(polygon_coords, str):
            logger.error(f"Invalid polygon coordinates: {polygon_coords}")
            raise HTTPException(status_code=400, detail="Invalid polygon coordinates")
        
        # Trim and validate coordinate string
        polygon_coords = polygon_coords.strip()
        if len(polygon_coords.split()) < 3:  # Ensure at least 3 coordinate pairs
            logger.error(f"Insufficient coordinates: {polygon_coords}")
            raise HTTPException(status_code=400, detail="Insufficient coordinates to form a polygon")
        
        # Prepare to store results
        road_results: Dict[str, List] = {}
        
        # Use httpx for concurrent requests
        async with httpx.AsyncClient(timeout=90.0) as client:  # Added timeout
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
                try:
                    response = await task
                    
                    # Log and handle errors
                    if response.status_code != 200:
                        logger.error(f"Overpass API error for {road_type}: {response.text}")
                        road_results[road_type] = []
                        continue
                    
                    # Parse and store results
                    road_data = response.json()
                    road_results[road_type] = road_data.get('elements', [])
                
                except httpx.RequestError as e:
                    logger.error(f"Request error for {road_type}: {str(e)}")
                    road_results[road_type] = []
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error for {road_type}: {str(e)}")
                    road_results[road_type] = []
        
        return road_results
    
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON request body")
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected server error")

# Health check endpoint
@app.get("/")
async def health_check():
    return {"status": "healthy"}
        
