from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from biaslens.analyzer import analyze as perform_analyze
from biaslens.analyzer import quick_analyze as perform_quick_analyze # Added import for quick_analyze

app = FastAPI(
    title="BiasLens API",
    description="API for analyzing text for bias and other characteristics using the BiasLens library.",
    version="0.1.0",
)

origins = [
    "http://localhost:3000",
    "https://bias-lens.vercel.app",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

