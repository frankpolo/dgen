from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import json

app = FastAPI()

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
        # Try to parse the body as JSON
        body = await request.json()
        print('body')
        print(body)
        print('reqjson')
        print(request.json())
        # Check if 'query' exists in the body
        if 'query' not in body:
            raise HTTPException(status_code=400, detail="Query is required")
        
        query = body['query']
        print('query')
        print(query)
        # Additional validation
        if not isinstance(query, str):
            raise HTTPException(status_code=400, detail="Query must be a string")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://overpass-api.de/api/interpreter', 
                content=query,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            print('response')
            print(response)
            # Check if request was successful
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, 
                    detail="Error querying Overpass API"
                )
            print('jjjson')
            print(response.json())
            return response.json()
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Optional health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
