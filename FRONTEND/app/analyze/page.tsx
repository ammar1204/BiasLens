"use client"

import { useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Loader2, AlertTriangle, CheckCircle, XCircle, Brain, TrendingUp, MessageSquare } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

// IMPORTANT: For Vercel deployment, ensure NEXT_PUBLIC_API_BASE_URL is set in environment variables
// to point to your backend API (e.g., your Render service URL).
// IMPORTANT: Ensure your backend API (e.g., on Render) has CORS configured to allow requests
// from your Vercel frontend domain.

"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Loader2, AlertTriangle, CheckCircle, XCircle, Brain, TrendingUp, MessageSquare, Info, Zap, EyeOff, Newspaper, Lightbulb } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"

// --- TypeScript Interfaces for API Responses ---

interface QuickAnalysisResult {
  score: number | null;
  indicator: string | null;
  explanation: string | null; // In quick_analyze, explanation is a string
  tip: string | null;
  // Quick analysis might have other specific fields, adjust as necessary
}

interface SentimentDetail {
  label: string;
  confidence: number;
  all_scores?: {
    negative?: number;
    neutral?: number;
    positive?: number;
  };
  headline_comparison?: any; // Define further if structure is known and used
  error?: string;
}

interface EmotionDetail {
  label: string;
  confidence: number;
  is_emotionally_charged?: boolean;
  manipulation_risk?: string;
  error?: string;
}

interface BiasTypeAnalysis {
  type: string | null;
  confidence: number | null;
  [key: string]: any; // For other model-specific scores
}

interface BiasDetail {
  flag: boolean;
  label: string | null;
  type_analysis: BiasTypeAnalysis | null;
  detected: boolean;
  error?: string;
}

interface NigerianPatternsDetail {
  has_triggers: boolean;
  has_clickbait: boolean;
  trigger_details?: string[] | Record<string, any>[];
  clickbait_details?: string[] | Record<string, any>[];
  error?: string;
}

interface FakeNewsDetail {
  detected: boolean;
  details?: {
    risk_level?: string;
    matched_phrases?: string[];
    [key: string]: any;
  };
  error?: string;
}

interface ViralManipulationDetail {
  engagement_bait_score?: number;
  sensationalism_score?: number;
  is_potentially_viral?: boolean;
  [key: string]: any; // For other virality metrics
  error?: string;
}

interface PatternDetail {
  nigerian_patterns: NigerianPatternsDetail | null;
  fake_news: FakeNewsDetail | null;
  viral_manipulation: ViralManipulationDetail | null;
  error?: string; // Top-level error for pattern analysis module itself
}

interface DetailedSubAnalysesResult {
  sentiment: SentimentDetail | null;
  emotion: EmotionDetail | null;
  bias: BiasDetail | null;
  patterns?: PatternDetail | null; // Optional if include_patterns is false
}

interface ComponentProcessingTimes {
  sentiment_analysis?: number;
  emotion_analysis?: number;
  bias_analysis?: number;
  pattern_analysis?: number;
  trust_score_calculation?: number;
  overall_assessment_generation?: number;
  [key: string]: number | undefined;
}

interface MetadataResult {
  component_processing_times: ComponentProcessingTimes | null;
  overall_processing_time_seconds: number | null;
  text_length?: number;
  initialized_components?: string[];
  analysis_timestamp?: number;
  error_message?: string; // If top-level analysis error
}

interface DeepAnalysisResult {
  trust_score: number | null;
  indicator: string | null;
  explanation: string[] | null; // In deep_analyze, explanation is an array of strings
  tip: string | null;
  primary_bias_type: string | null;
  metadata: MetadataResult | null;
  detailed_sub_analyses?: DetailedSubAnalysesResult | null; // Optional based on include_detailed_results
}

type AnalysisResultType = QuickAnalysisResult | DeepAnalysisResult | null;
type AnalysisMode = "quick" | "deep" | null;

export default function AnalyzePage() {
  const { user, loading: authLoading } = useAuth()
  const [text, setText] = useState("")
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<AnalysisResultType>(null)
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const { toast } = useToast()
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/signin")
    }
  }, [user, authLoading, router])

  const handleAnalyze = async () => {
    if (!text.trim()) {
      toast({ title: "Error", description: "Please enter some text to analyze", variant: "destructive" })
      return
    }

    setAnalyzing(true)
    setResult(null)
    setApiError(null)
    setAnalysisMode("quick")

    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || ""; // Default to relative path if not set
      const response = await fetch(`${apiBaseUrl}/quick_analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.trim() }), // Removed userId
      })

      const responseData = await response.json();
      if (!response.ok) {
        throw new Error(responseData.detail || responseData.error || "Quick analysis failed")
      }
      setResult(responseData as QuickAnalysisResult)
      toast({ title: "Quick Analysis Complete", description: "Text analyzed successfully!" })
    } catch (error: any) {
      console.error("Quick Analysis API Error:", error);
      const errorMsg = error.message || "Failed to analyze text. Please try again.";
      setApiError(errorMsg)
      toast({ title: "Error", description: errorMsg, variant: "destructive" })
    } finally {
      setAnalyzing(false)
    }
  }

  const handleDeepAnalyze = async () => {
    if (!text.trim()) {
      toast({ title: "Error", description: "Please enter some text to analyze", variant: "destructive" })
      return
    }

    setAnalyzing(true)
    setResult(null)
    setApiError(null)
    setAnalysisMode("deep")

    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || ""; // Default to relative path if not set
      const requestBody = {
        text: text.trim(),
        include_detailed_results: true,
        include_patterns: true,
      };
      const response = await fetch(`${apiBaseUrl}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody), // Removed userId, added params
      })

      const responseData = await response.json();
      if (!response.ok) {
         throw new Error(responseData.detail || responseData.error || "Deep analysis failed")
      }
      setResult(responseData as DeepAnalysisResult)
      toast({ title: "Deep Analysis Complete", description: "Text deeply analyzed successfully!" })
    } catch (error: any) {
      console.error("Deep Analysis API Error:", error);
      const errorMsg = error.message || "Failed to deeply analyze text. Please try again.";
      setApiError(errorMsg)
      toast({ title: "Error", description: errorMsg, variant: "destructive" })
    } finally {
      setAnalyzing(false)
    }
  }

  const getTrustScoreColor = (score: number | null) => {
    if (score === null) return "text-gray-600";
    if (score >= 70) return "text-green-600";
    if (score >= 40) return "text-yellow-600";
    return "text-red-600";
  }

  const getSentimentIcon = (sentimentLabel: string | undefined) => {
    if (!sentimentLabel) return <MessageSquare className="h-5 w-5 text-gray-600" />;
    switch (sentimentLabel.toLowerCase()) {
      case "positive": return <CheckCircle className="h-5 w-5 text-green-600" />;
      case "negative": return <XCircle className="h-5 w-5 text-red-600" />;
      default: return <MessageSquare className="h-5 w-5 text-gray-600" />;
    }
  }

  // Helper function to render individual sub-analysis details
  const renderSubDetail = (title: string, data: any, icon?: React.ReactNode) => {
    if (!data || (typeof data === 'object' && data.error)) {
      return (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2">{icon || <Info />} {title}</CardTitle></CardHeader>
          <CardContent><p className="text-red-500">{data?.error || "Data not available or analysis error."}</p></CardContent>
        </Card>
      );
    }
    // Add more specific rendering for each type of data if needed
    return (
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2">{icon || <Info />} {title}</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm">
          {Object.entries(data).map(([key, value]) => {
            if (typeof value === 'object' && value !== null) {
              return <div key={key}><span className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</span> <pre className="whitespace-pre-wrap text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded">{JSON.stringify(value, null, 2)}</pre></div>;
            }
            return <div key={key}><span className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</span> {String(value)}</div>;
          })}
        </CardContent>
      </Card>
    );
  };


  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!user) {
    // This will be handled by the useEffect redirect, but good for clarity
    return null
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="text-center mb-8">
        <h1 className="text-3xl md:text-4xl font-bold mb-4">BiasLens Text Analyzer</h1>
        <p className="text-lg text-muted-foreground">
          Paste text to analyze for bias, sentiment, emotional tone, and more.
        </p>
      </div>

      {/* Input Section */}
      <Card className="mb-8 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Brain className="h-6 w-6 text-primary" />
            Analyze Content
          </CardTitle>
          <CardDescription>Enter text (articles, posts, etc.) for AI-powered analysis.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            placeholder="Paste your text here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="min-h-[200px] text-base border-gray-300 focus:border-primary"
            maxLength={10000} // Increased max length
          />
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <span className="text-sm text-muted-foreground">{text.length}/10000 characters</span>
            <div className="flex gap-4">
              <Button onClick={handleAnalyze} disabled={analyzing || !text.trim()} size="lg" variant="outline">
                {analyzing && analysisMode === 'quick' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Quick Analysis
              </Button>
              <Button onClick={handleDeepAnalyze} disabled={analyzing || !text.trim()} size="lg">
                {analyzing && analysisMode === 'deep' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Deep Analysis
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {apiError && (
        <Card className="mb-8 bg-red-50 dark:bg-red-900 border-red-500 dark:border-red-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-700 dark:text-red-300">
              <AlertTriangle /> Analysis Error
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-600 dark:text-red-400">{apiError}</p>
          </CardContent>
        </Card>
      )}

      {/* Results Section */}
      {result && !apiError && (
        <div className="space-y-6">
          {/* Common Results: Trust Score, Indicator, Explanation, Tip */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Overall Assessment
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {(analysisMode === 'deep' && (result as DeepAnalysisResult).trust_score !== null) || (analysisMode === 'quick' && (result as QuickAnalysisResult).score !== null) ? (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold">
                      <span className={getTrustScoreColor(analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score)}>
                        {analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score}%
                      </span>
                      <span className="text-xl ml-1">Trust Score</span>
                    </span>
                    <Badge variant={
                      (analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score ?? 0 : (result as QuickAnalysisResult).score ?? 0) >= 70 ? "default"
                      : (analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score ?? 0 : (result as QuickAnalysisResult).score ?? 0) >= 40 ? "secondary"
                      : "destructive"
                    }>
                      {result.indicator || "N/A"}
                    </Badge>
                  </div>
                  <Progress value={analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score} className="h-3" />
                </>
              ) : <p className="text-muted-foreground">Trust score not available.</p>}

              <div className="mt-4">
                <h4 className="font-semibold mb-1">Explanation:</h4>
                {Array.isArray(result.explanation) ?
                  (result.explanation as string[]).map((line, index) => <p key={index} className="text-muted-foreground leading-relaxed">{line}</p>) :
                  <p className="text-muted-foreground leading-relaxed">{result.explanation || "No explanation provided."}</p>
                }
              </div>
              <div className="mt-4">
                <h4 className="font-semibold mb-1">Tip:</h4>
                <p className="text-muted-foreground leading-relaxed flex items-start gap-2">
                  <Lightbulb className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-1" />
                  <span>{result.tip || "No specific tip provided."}</span>
                </p>
              </div>

              {analysisMode === 'deep' && (result as DeepAnalysisResult).primary_bias_type && (
                <div className="mt-4">
                  <h4 className="font-semibold mb-1">Primary Bias Type Detected:</h4>
                  <Badge variant="secondary" className="capitalize">{(result as DeepAnalysisResult).primary_bias_type}</Badge>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Deep Analysis Specific Details */}
          {analysisMode === 'deep' && (result as DeepAnalysisResult).detailed_sub_analyses && (
            <>
              <h2 className="text-2xl font-semibold mt-8 mb-4 border-b pb-2">Detailed Sub-Analyses</h2>
              <div className="grid md:grid-cols-2 gap-6">
                {renderSubDetail("Sentiment Analysis", (result as DeepAnalysisResult).detailed_sub_analyses?.sentiment, <MessageSquare />)}
                {renderSubDetail("Emotion Analysis", (result as DeepAnalysisResult).detailed_sub_analyses?.emotion, <Zap />)}
                {renderSubDetail("Bias Analysis", (result as DeepAnalysisResult).detailed_sub_analyses?.bias, <EyeOff />)}
                {(result as DeepAnalysisResult).detailed_sub_analyses?.patterns && renderSubDetail("Pattern Analysis", (result as DeepAnalysisResult).detailed_sub_analyses?.patterns, <Newspaper />)}
              </div>
            </>
          )}

          {/* Metadata for Deep Analysis */}
          {analysisMode === 'deep' && (result as DeepAnalysisResult).metadata && (
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Info className="h-5 w-5" />
                  Analysis Metadata
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground space-y-1">
                <p><strong>Overall Processing Time:</strong> {(result as DeepAnalysisResult).metadata?.overall_processing_time_seconds?.toFixed(4)} seconds</p>
                <p><strong>Text Length:</strong> {(result as DeepAnalysisResult).metadata?.text_length} characters</p>
                <div><strong>Component Times (ms):</strong>
                  <ul className="list-disc pl-5">
                    {Object.entries((result as DeepAnalysisResult).metadata?.component_processing_times || {}).map(([key, value]) => (
                      <li key={key}><span className="capitalize">{key.replace(/_/g, ' ')}:</span> {(value * 1000).toFixed(2)} ms</li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
