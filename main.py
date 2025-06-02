from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, List, Optional, Dict, Any # Added List, Dict, Any
from typing import Optional # typing.Optional is already imported via pydantic, but explicit is fine

from biaslens.analyzer import analyze as perform_analyze
from biaslens.analyzer import quick_analyze as perform_quick_analyze

# --- Pydantic Models for /analyze Response ---

class SentimentDetailsModel(BaseModel):
    label: Optional[str] = None
    confidence: Optional[float] = None

class EmotionDetailsModel(BaseModel):
    label: Optional[str] = None
    confidence: Optional[float] = None
    is_emotionally_charged: Optional[bool] = None
    manipulation_risk: Optional[str] = None

class BiasDetailsModel(BaseModel):
    detected: Optional[bool] = None
    label: Optional[str] = None
    confidence: Optional[float] = None # Confidence of the bias type classification

class PatternHighlightsModel(BaseModel):
    nigerian_context_detected: Optional[bool] = None
    clickbait_detected: Optional[bool] = None
    fake_news_risk: Optional[str] = None

class LightweightNigerianBiasAssessmentModel(BaseModel):
    inferred_bias_type: Optional[str] = None
    bias_category: Optional[str] = None
    bias_target: Optional[str] = None
    matched_keywords: Optional[List[str]] = None

class DetailedSubAnalysesModel(BaseModel):
    sentiment: Optional[Dict[str, Any]] = None
    emotion: Optional[Dict[str, Any]] = None
    bias: Optional[Dict[str, Any]] = None
    patterns: Optional[Dict[str, Any]] = None
    lightweight_nigerian_bias: Optional[LightweightNigerianBiasAssessmentModel] = None

class AnalyzeResponseModel(BaseModel):
    trust_score: Optional[float] = None
    indicator: Optional[str] = None
    explanation: Optional[List[str]] = None
    tip: Optional[str] = None
    primary_bias_type: Optional[str] = None
    bias_details: Optional[BiasDetailsModel] = None
    sentiment_details: Optional[SentimentDetailsModel] = None
    emotion_details: Optional[EmotionDetailsModel] = None
    pattern_highlights: Optional[PatternHighlightsModel] = None
    lightweight_nigerian_bias_assessment: Optional[LightweightNigerianBiasAssessmentModel] = None
    detailed_sub_analyses: Optional[DetailedSubAnalysesModel] = None

# --- Pydantic Model for /quick_analyze Response (Optional, but good practice) ---
# Based on the structure of quick_analyze output in analyzer.py
class QuickAnalysisResponseModel(BaseModel):
    score: Optional[float] = None
    indicator: Optional[str] = None
    explanation: Optional[str] = None
    tip: Optional[str] = None
    inferred_bias_type: Optional[str] = None
    bias_category: Optional[str] = None
    bias_target: Optional[str] = None
    matched_keywords: Optional[List[str]] = None


app = FastAPI(
    title="BiasLens API",
    description="API for analyzing text for bias and other characteristics using the BiasLens library.",
    version="0.1.0",
)

origins = [
    "http://localhost:3000",
    "https_bias-lens.vercel.app", # Corrected: Remove underscore, use https://
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
    headline: Optional[str] = None
    include_patterns: bool = True # Defaulting to True as per BiasLensAnalyzer.analyze
    include_detailed_results: bool = False # Defaulting to False

@app.get("/")
async def read_root():
    return {"message": "Welcome to the BiasLens API!"}

@app.post("/analyze", response_model=AnalyzeResponseModel)
async def analyze_text(request: TextAnalysisRequest):
    '''
    Performs comprehensive analysis on the provided text.
    '''
    analysis_results = perform_analyze(
        text=request.text,
        headline=request.headline,
        include_patterns=request.include_patterns,
        include_detailed_results=request.include_detailed_results
    )
    return analysis_results

@app.post("/quick_analyze", response_model=QuickAnalysisResponseModel) # Added response model
async def quick_analyze_text(request: TextAnalysisRequest): # Using same request model, though not all fields are used by quick_analyze
    '''
    Performs a quick analysis on the provided text.
    '''
    # perform_quick_analyze only takes 'text'
    quick_analysis_results = perform_quick_analyze(
        text=request.text
    )
    return quick_analysis_results

# Further endpoints will be added here if needed.
