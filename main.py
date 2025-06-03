from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel # Removed List, Optional, Dict, Any from here
from typing import List, Optional, Dict, Any # Added these types from typing

from biaslens.analyzer import analyze as perform_analyze
from biaslens.analyzer import quick_analyze as perform_quick_analyze

# --- Pydantic Models for /analyze Response ("Core Solution" Structure) ---

class ToneAnalysisModel(BaseModel):
    primary_tone: Optional[str] = None
    is_emotionally_charged: Optional[bool] = None
    emotional_manipulation_risk: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_confidence: Optional[float] = None

class BiasAnalysisModel(BaseModel):
    primary_bias_type: Optional[str] = None
    bias_strength_label: Optional[str] = None
    ml_model_confidence: Optional[float] = None
    source_of_primary_bias: Optional[str] = None

class ManipulationAnalysisModel(BaseModel):
    is_clickbait: Optional[bool] = None
    engagement_bait_score: Optional[float] = None
    sensationalism_score: Optional[float] = None

class VeracitySignalsModel(BaseModel):
    fake_news_risk_level: Optional[str] = None
    matched_suspicious_phrases: Optional[List[str]] = None

# --- Reused Models ---

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

# --- Main Response Model for /analyze ---

class AnalyzeResponseModel(BaseModel):
    trust_score: Optional[float] = None
    indicator: Optional[str] = None
    explanation: Optional[List[str]] = None
    tip: Optional[str] = None

    tone_analysis: Optional[ToneAnalysisModel] = None
    bias_analysis: Optional[BiasAnalysisModel] = None
    manipulation_analysis: Optional[ManipulationAnalysisModel] = None
    veracity_signals: Optional[VeracitySignalsModel] = None

    lightweight_nigerian_bias_assessment: Optional[LightweightNigerianBiasAssessmentModel] = None
    detailed_sub_analyses: Optional[DetailedSubAnalysesModel] = None

# --- Pydantic Models for /quick_analyze Response ("Core Solution" Aligned) ---

class QuickToneAnalysisModel(BaseModel):
    sentiment_label: Optional[str] = None
    sentiment_confidence: Optional[float] = None

class QuickManipulationAnalysisModel(BaseModel):
    is_clickbait: Optional[bool] = None

class QuickVeracitySignalsModel(BaseModel):
    fake_news_risk_level: Optional[str] = None
    matched_suspicious_phrases: Optional[List[str]] = None


class QuickAnalysisResponseModel(BaseModel):
    score: Optional[float] = None
    indicator: Optional[str] = None
    explanation: Optional[str] = None
    tip: Optional[str] = None

    tone_analysis: Optional[QuickToneAnalysisModel] = None
    bias_analysis: Optional[LightweightNigerianBiasAssessmentModel] = None
    manipulation_analysis: Optional[QuickManipulationAnalysisModel] = None
    veracity_signals: Optional[QuickVeracitySignalsModel] = None

# --- Request Models ---

class TextAnalysisRequest(BaseModel): # For /analyze endpoint
    text: str
    headline: Optional[str] = None
    include_patterns: bool = True
    include_detailed_results: bool = False

class QuickAnalysisRequest(BaseModel): # For /quick_analyze endpoint
    text: str

app = FastAPI(
    title="BiasLens API",
    description="API for analyzing text for bias and other characteristics using the BiasLens library.",
    version="0.1.0",
)

origins = [
    "http://localhost:3000",
    "https://bias-lens.vercel.app",
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/quick_analyze", response_model=QuickAnalysisResponseModel)
async def quick_analyze_text(request: QuickAnalysisRequest):
    '''
    Performs a quick analysis on the provided text.
    '''
    quick_analysis_results = perform_quick_analyze(
        text=request.text
    )
    return quick_analysis_results
