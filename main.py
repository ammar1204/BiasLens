from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Added import
from pydantic import BaseModel
from typing import Optional

from biaslens.analyzer import analyze as perform_analyze
from biaslens.analyzer import quick_analyze as perform_quick_analyze

app = FastAPI(
    title="BiasLens API",
    description="API for analyzing text for bias and other characteristics using the BiasLens library.",
    version="0.1.0",
)

# CORS Configuration
# IMPORTANT: Replace this placeholder with your actual Vercel frontend URL once deployed!
# Example: VERCEL_FRONTEND_URL = "https://your-project-name.vercel.app"
VERCEL_FRONTEND_URL = "https://your-vercel-app-url.vercel.app"  # <<< USER MUST REPLACE THIS!

origins = [
    VERCEL_FRONTEND_URL,
    "http://localhost:3000",    # For local Next.js development (default port)
    "http://127.0.0.1:3000",   # Alternative for local Next.js development
    # Add any other origins if necessary (e.g., staging frontend URL)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # Allows specific origins to make requests
    allow_credentials=True,     # Allows cookies to be included in cross-origin requests
    allow_methods=["*"],          # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],          # Allows all headers
)

class TextAnalysisRequest(BaseModel):
    text: str
    # Optional: Add other parameters like headline if your frontend might send them
    # For now, keeping it simple as per the current understanding.
    # headline: Optional[str] = None
    # include_patterns: bool = True
    # include_detailed_results: bool = False

@app.get("/")
async def read_root():
    return {"message": "Welcome to the BiasLens API!"}

@app.post("/analyze")
async def analyze_text(request: TextAnalysisRequest):
    '''
    Performs comprehensive analysis on the provided text.
    '''
    analysis_results = perform_analyze(
        text=request.text
    )
    return analysis_results

@app.post("/quick_analyze")
async def quick_analyze_text(request: TextAnalysisRequest):
    '''
    Performs a quick analysis on the provided text.
    '''
    quick_analysis_results = perform_quick_analyze(
        text=request.text
    )
    return quick_analysis_results

# Further endpoints will be added here if needed.
