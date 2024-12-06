from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/roads")
async def query_overpass(request: Request):
    try:
        # Try to get the body content
        body_raw = await request.body()
        logger.debug(f"Raw request body: {body_raw}")

        # Check if the body is already a valid Overpass query string
        if body_raw and body_raw.startswith(b'[out:json]'):
            query = body_raw.decode('utf-8')
        else:
            # Try to parse as JSON
            try:
                body = await request.json()
                logger.debug(f"Parsed JSON body: {body}")
                
                # Extract query, supporting different input formats
                query = body.get('query')
                if not query:
                    raise ValueError("No query found in request body")
            
            except Exception as json_error:
                logger.error(f"JSON parsing error: {json_error}")
                raise HTTPException(status_code=400, detail=f"Invalid request: {str(json_error)}")

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

@app.post("/api2/roads")
async def query_overpass(request: Request):
    try:
        # Parse JSON request body
        body = await request.json()
        
        # Extract roadType and polygonCoords
        road_type = body.get('roadType')
        polygon_coords = body.get('polygonCoords')
        
        # Validate inputs
        if not road_type or not polygon_coords:
            raise HTTPException(status_code=400, detail="Missing roadType or polygonCoords")

        # Construct Overpass query dynamically
        query = f"""
        [out:json];
        way["highway"="{road_type}"](poly:"{polygon_coords}");
        (._;>;);
        out body geom;
        """

        # Log the query for debugging
        logger.debug(f"Constructed Overpass query: {query}")

        # Make Overpass API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://overpass-api.de/api/interpreter', 
                content=query,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Log response details
            logger.debug(f"API response status: {response.status_code}")
            
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

@app.post("/api3/roads")
async def query_overpass(request: Request):
    try:
        # Parse JSON request body
        body = await request.json()
        
        # Extract roadType and polygonCoords
        road_type = body.get('roadType')
        polygon_coords = body.get('polygonCoords')
        
        # Validate inputs
        if not road_type or not polygon_coords:
            raise HTTPException(status_code=400, detail="Missing roadType or polygonCoords")

        # Construct Overpass query dynamically
        query = f"""
        [out:json];
        way["highway"="{road_type}"](poly:"{polygon_coords}");
        (._;>;);
        out body geom;
        """

        # Log the query for debugging
        logger.debug(f"Constructed Overpass query: {query}")

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
            
            return response.json()['elements']
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")



# Health check endpoint
@app.get("/")
async def health_check():
    return {"status": "healthy"}
