from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json

app = FastAPI()

# CORS allow
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# REAL API URL (Clone Source)
# ============================================
REAL_API_URL = "https://tg-to-number-number-nitin.vercel.app/api"

# ============================================
# CLONE API ENDPOINT
# ============================================
@app.get("/api")
async def clone_api(search: str = Query(..., description="Phone number or Telegram ID")):
    """
    Clone API - Exact same response as original,
    but with custom owner and channel
    """
    
    try:
        # Step 1: Call the real API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(REAL_API_URL, params={"search": search})
            
            if response.status_code == 200:
                # Step 2: Get real data
                real_data = response.json()
                
                # Step 3: Modify ONLY owner and channel
                # Keep everything else EXACTLY the same
                if "metadata" in real_data:
                    real_data["metadata"]["owner"] = "@RD3B4T"
                    real_data["metadata"]["channel"] = "https://t.me/RD3B4T"
                else:
                    # If metadata doesn't exist, create it
                    real_data["metadata"] = {
                        "owner": "@RD3B4T",
                        "channel": "https://t.me/RD3B4T",
                        "api_version": "1.0.0"
                    }
                
                return JSONResponse(real_data)
            
            else:
                # If real API fails, return fallback response
                return JSONResponse({
                    "location": {
                        "country": "India",
                        "country_code": "+91",
                        "phone_number": search
                    },
                    "userid_info": {
                        "name": f"User {search}",
                        "telegram_id": search,
                        "username": "N/A"
                    },
                    "metadata": {
                        "owner": "@RD3B4T",
                        "channel": "https://t.me/RD3B4T",
                        "api_version": "1.0.0"
                    }
                })
                
    except Exception as e:
        # Error fallback
        return JSONResponse({
            "location": {
                "country": "India",
                "country_code": "+91",
                "phone_number": search
            },
            "userid_info": {
                "name": f"User {search}",
                "telegram_id": search,
                "username": "N/A"
            },
            "metadata": {
                "owner": "@RD3B4T",
                "channel": "https://t.me/RD3B4T",
                "api_version": "1.0.0"
            }
        })

# ============================================
# ROOT ENDPOINT
# ============================================
@app.get("/")
async def root():
    return {
        "status": "✅ API is live",
        "developer": "@RD3B4T",
        "channel": "https://t.me/RD3B4T",
        "endpoint": "/api?search=9235307936"
    }

# ============================================
# HEALTH CHECK
# ============================================
@app.get("/health")
async def health():
    return {"status": "healthy", "developer": "@RD3B4T"}
              
