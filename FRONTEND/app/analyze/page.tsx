"use client";

// IMPORTANT: For Vercel deployment, ensure NEXT_PUBLIC_API_BASE_URL is set in environment variables
// to point to your backend API (e.g., your Render service URL).
// IMPORTANT: Ensure your backend API (e.g., on Render) has CORS configured to allow requests
// from your Vercel frontend domain.

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Loader2, AlertTriangle, CheckCircle, XCircle, Brain, TrendingUp, MessageSquare, Info, Zap, EyeOff, Newspaper, Lightbulb, Gauge, Palette, Fingerprint, Sparkles } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useRouter } from "next/navigation";

// --- TypeScript Interfaces for API Responses ---

interface QuickAnalysisResult {
  score: number | null;
  indicator: string | null;
  explanation: string | null;
  tip: string | null;
  inferred_bias_type?: string | null;
  bias_category?: string | null;
  bias_target?: string | null;
  matched_keywords?: string[] | null;
}

// --- New/Updated Interfaces for Deep Analysis (/analyze endpoint) ---

interface SentimentDetailsModel {
  label?: string | null;
  confidence?: number | null;
}

interface EmotionDetailsModel {
  label?: string | null;
  confidence?: number | null;
  is_emotionally_charged?: boolean | null;
  manipulation_risk?: string | null;
}

interface BiasDetailsModel {
  detected?: boolean | null;
  label?: string | null; 
  confidence?: number | null; 
}

interface PatternHighlightsModel {
  nigerian_context_detected?: boolean | null;
  clickbait_detected?: boolean | null;
  fake_news_risk?: string | null;
}

interface LightweightNigerianBiasAssessmentModel {
  inferred_bias_type?: string | null;
  bias_category?: string | null;
  bias_target?: string | null;
  matched_keywords?: string[] | null;
}

// Interfaces for the content of `detailed_sub_analyses`
interface SentimentDetail { 
  label: string;
  confidence: number;
  all_scores?: {
    negative?: number;
    neutral?: number;
    positive?: number;
  };
  headline_comparison?: any; 
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
  [key: string]: any; 
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
    is_clickbait?: boolean; 
    [key: string]: any;
  };
  error?: string;
}

interface ViralManipulationDetail { 
  engagement_bait_score?: number;
  sensationalism_score?: number;
  is_potentially_viral?: boolean;
  [key: string]: any; 
  error?: string;
}

interface PatternDetail { 
  nigerian_patterns: NigerianPatternsDetail | null;
  fake_news: FakeNewsDetail | null;
  viral_manipulation: ViralManipulationDetail | null;
  error?: string; 
}

interface DetailedSubAnalysesResult {
  sentiment: SentimentDetail | null;
  emotion: EmotionDetail | null;
  bias: BiasDetail | null;
  patterns?: PatternDetail | null; 
  lightweight_nigerian_bias?: LightweightNigerianBiasAssessmentModel | null; 
}

// Main interface for Deep Analysis results
interface DeepAnalysisResult {
  trust_score: number | null;
  indicator: string | null;
  explanation: string[] | null; 
  tip: string | null;
  primary_bias_type: string | null;
  
  sentiment_details?: SentimentDetailsModel | null;
  emotion_details?: EmotionDetailsModel | null;
  bias_details?: BiasDetailsModel | null;
  pattern_highlights?: PatternHighlightsModel | null;
  lightweight_nigerian_bias_assessment?: LightweightNigerianBiasAssessmentModel | null;

  detailed_sub_analyses?: DetailedSubAnalysesResult | null; 
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

  const handleAnalyze = async () => { // This is for Quick Analysis
    if (!text.trim()) {
      toast({ title: "Error", description: "Please enter some text to analyze", variant: "destructive" })
      return
    }

    setAnalyzing(true)
    setResult(null)
    setApiError(null)
    setAnalysisMode("quick")

    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || ""; 
      const response = await fetch(`${apiBaseUrl}/quick_analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.trim() }),
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

  const handleDeepAnalyze = async () => { // This is for Deep Analysis
    if (!text.trim()) {
      toast({ title: "Error", description: "Please enter some text to analyze", variant: "destructive" })
      return
    }

    setAnalyzing(true)
    setResult(null)
    setApiError(null)
    setAnalysisMode("deep")

    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || ""; 
      const requestBody = {
        text: text.trim(),
        include_detailed_results: true,
        include_patterns: true,
      };
      const response = await fetch(`${apiBaseUrl}/analyze`, { 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
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
  
  const renderSubDetail = (title: string, data: any, icon?: React.ReactNode) => {
    // Check if data is null, undefined, or an empty object
    if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
        // If it's explicitly an error object with only an error key, show specific message
        if (data && typeof data === 'object' && data.error && Object.keys(data).length === 1) {
             return (
                <Card>
                  <CardHeader><CardTitle className="flex items-center gap-2 text-base">{icon || <Info />} {title}</CardTitle></CardHeader>
                  <CardContent><p className="text-sm text-red-500">{data.error}</p></CardContent>
                </Card>
            );
        }
        // For other cases of no data or empty object
        return (
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2 text-base">{icon || <Info />} {title}</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-muted-foreground">Data not available or not applicable for this item.</p></CardContent>
            </Card>
        );
    }

    // Filter out entries where value is null or undefined to avoid rendering empty fields
    const validEntries = Object.entries(data).filter(([_, value]) => value !== null && value !== undefined);

    if (validEntries.length === 0 || (validEntries.length === 1 && validEntries[0][0] === 'error' && validEntries[0][1])) {
         return (
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2 text-base">{icon || <Info />} {title}</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-muted-foreground">{data.error || "Data not available or not applicable for this item."}</p></CardContent>
            </Card>
        );
    }
    
    return (
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2 text-base">{icon || <Info />} {title}</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm">
          {validEntries.map(([key, value]) => {
            if (key === 'error' && value) return null; 
            if (typeof value === 'boolean') {
                 return <div key={key}><span className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</span> {value ? "Yes" : "No"}</div>;
            }
            if (typeof value === 'object' && value !== null) {
              const contentToPrint = JSON.stringify(value, null, 2);
              if (contentToPrint === '{}' || contentToPrint === '[]') return null;
              return <div key={key} className="break-all"><span className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</span> <pre className="whitespace-pre-wrap text-xs bg-muted p-2 rounded mt-1">{contentToPrint}</pre></div>;
            }
            return <div key={key}><span className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</span> {String(value)}</div>;
          })}
        </CardContent>
      </Card>
    );
  };

  const renderTopLevelDetails = (res: DeepAnalysisResult) => {
    // Only render the section if at least one of the detail objects is present
    if (!res.sentiment_details && !res.emotion_details && !res.bias_details && !res.pattern_highlights) {
      return null;
    }
    return (
      <>
        <h2 className="text-2xl font-semibold mt-8 mb-4 border-b pb-2">Analysis Summaries</h2>
        <div className="grid md:grid-cols-2 gap-6">
          {res.sentiment_details && renderSubDetail("Sentiment Summary", res.sentiment_details, <MessageSquare />)}
          {res.emotion_details && renderSubDetail("Emotion Summary", res.emotion_details, <Zap />)}
          {res.bias_details && renderSubDetail("Bias Summary (ML)", res.bias_details, <EyeOff />)}
          {res.pattern_highlights && renderSubDetail("Pattern Highlights", res.pattern_highlights, <Fingerprint />)}
        </div>
      </>
    )
  }

  if (authLoading) {
    return ( <div className="flex items-center justify-center min-h-screen"> <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div> </div> )
  }
  if (!user) { return null }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="text-center mb-8">
        <h1 className="text-3xl md:text-4xl font-bold mb-4">BiasLens Text Analyzer</h1>
        <p className="text-lg text-muted-foreground"> Paste text to analyze for bias, sentiment, emotional tone, and more. </p>
      </div>

      <Card className="mb-8 shadow-lg">
        <CardHeader> <CardTitle className="flex items-center gap-2 text-xl"> <Brain className="h-6 w-6 text-primary" /> Analyze Content </CardTitle> <CardDescription>Enter text (articles, posts, etc.) for AI-powered analysis.</CardDescription> </CardHeader>
        <CardContent className="space-y-4">
          <Textarea placeholder="Paste your text here..." value={text} onChange={(e) => setText(e.target.value)} className="min-h-[200px] text-base border-gray-300 focus:border-primary" maxLength={10000} />
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <span className="text-sm text-muted-foreground">{text.length}/10000 characters</span>
            <div className="flex gap-4">
              <Button onClick={handleAnalyze} disabled={analyzing || !text.trim()} size="lg" variant="outline"> {analyzing && analysisMode === 'quick' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Quick Analysis </Button>
              <Button onClick={handleDeepAnalyze} disabled={analyzing || !text.trim()} size="lg"> {analyzing && analysisMode === 'deep' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Deep Analysis </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {apiError && ( <Card className="mb-8 bg-red-50 dark:bg-red-900 border-red-500 dark:border-red-700"> <CardHeader> <CardTitle className="flex items-center gap-2 text-red-700 dark:text-red-300"> <AlertTriangle /> Analysis Error </CardTitle> </CardHeader> <CardContent> <p className="text-red-600 dark:text-red-400">{apiError}</p> </CardContent> </Card> )}

      {result && !apiError && (
        <div className="space-y-6">
          <Card>
            <CardHeader> <CardTitle className="flex items-center gap-2"> <Gauge className="h-5 w-5 text-primary" /> Overall Assessment </CardTitle> </CardHeader>
            <CardContent className="space-y-4">
              {((analysisMode === 'deep' && (result as DeepAnalysisResult).trust_score !== null) || (analysisMode === 'quick' && (result as QuickAnalysisResult).score !== null)) ? (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold">
                      <span className={getTrustScoreColor(analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score)}>
                        {analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score}%
                      </span>
                      <span className="text-xl ml-1">Trust Score</span>
                    </span>
                    <Badge variant={ (((analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score) ?? 0) >= 70 ? "default" : (((analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score) ?? 0) >= 40 ? "secondary" : "destructive")) }>
                      {result.indicator || "N/A"}
                    </Badge>
                  </div>
                  <Progress value={(analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score)} className="h-3" />
                </>
              ) : <p className="text-muted-foreground">Trust score not available.</p>}
              <div className="mt-4">
                <h4 className="font-semibold mb-1">Explanation:</h4>
                {Array.isArray(result.explanation) ? (result.explanation as string[]).map((line, index) => <p key={index} className="text-muted-foreground leading-relaxed">{line}</p>) : <p className="text-muted-foreground leading-relaxed">{result.explanation || "No explanation provided."}</p> }
              </div>
              <div className="mt-4">
                <h4 className="font-semibold mb-1">Tip:</h4>
                <p className="text-muted-foreground leading-relaxed flex items-start gap-2"> <Lightbulb className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-1" /> <span>{result.tip || "No specific tip provided."}</span> </p>
              </div>
              {analysisMode === 'deep' && (result as DeepAnalysisResult).primary_bias_type && (
                <div className="mt-4"> <h4 className="font-semibold mb-1">Primary Bias Type Detected:</h4> <Badge variant="secondary" className="capitalize">{(result as DeepAnalysisResult).primary_bias_type}</Badge> </div>
              )}
            </CardContent>
          </Card>
          
          {analysisMode === 'deep' && renderTopLevelDetails(result as DeepAnalysisResult)}

          {( (result as QuickAnalysisResult | DeepAnalysisResult).lightweight_nigerian_bias_assessment?.inferred_bias_type &&
            (result as QuickAnalysisResult | DeepAnalysisResult).lightweight_nigerian_bias_assessment?.inferred_bias_type !== "No specific patterns detected" &&
            (result as QuickAnalysisResult | DeepAnalysisResult).lightweight_nigerian_bias_assessment?.inferred_bias_type !== "Nigerian context detected, specific bias type unclear from patterns") &&
          (
            <Card>
              <CardHeader> <CardTitle className="flex items-center gap-2"> <Sparkles className="h-5 w-5 text-purple-500" /> Lightweight Nigerian Bias Assessment </CardTitle> <CardDescription>Rule-based detection of Nigerian-specific bias patterns.</CardDescription> </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div><span className="font-semibold">Inferred Bias Type:</span> {(result as QuickAnalysisResult | DeepAnalysisResult).lightweight_nigerian_bias_assessment!.inferred_bias_type}</div>
                {(result as QuickAnalysisResult | DeepAnalysisResult).lightweight_nigerian_bias_assessment!.bias_category && <div><span className="font-semibold">Category:</span> <Badge variant="outline">{(result as QuickAnalysisResult | DeepAnalysisResult).lightweight_nigerian_bias_assessment!.bias_category}</Badge></div>}
                {(result as QuickAnalysisResult | DeepAnalysisResult).lightweight_nigerian_bias_assessment!.bias_target && <div><span className="font-semibold">Target:</span> <Badge variant="outline">{(result as QuickAnalysisResult | DeepAnalysisResult).lightweight_nigerian_bias_assessment!.bias_target}</Badge></div>}
                {(result as QuickAnalysisResult | DeepAnalysisResult).lightweight_nigerian_bias_assessment!.matched_keywords && (result as QuickAnalysisResult | DeepAnalysisResult).lightweight_nigerian_bias_assessment!.matched_keywords!.length > 0 && (
                  <div> <span className="font-semibold">Matched Keywords:</span> <div className="flex flex-wrap gap-1 mt-1"> {(result as QuickAnalysisResult | DeepAnalysisResult).lightweight_nigerian_bias_assessment!.matched_keywords!.map(keyword => ( <Badge key={keyword} variant="secondary" className="text-xs">{keyword}</Badge> ))} </div> </div>
                )}
              </CardContent>
            </Card>
          )}
          
          {analysisMode === 'deep' && (result as DeepAnalysisResult).detailed_sub_analyses && (
            <>
              <h2 className="text-2xl font-semibold mt-8 mb-4 border-b pb-2">Detailed Sub-Analyses</h2>
              <div className="grid md:grid-cols-2 gap-6">
                {renderSubDetail("Sentiment Details (Full)", (result as DeepAnalysisResult).detailed_sub_analyses?.sentiment, <MessageSquare />)}
                {renderSubDetail("Emotion Details (Full)", (result as DeepAnalysisResult).detailed_sub_analyses?.emotion, <Zap />)}
                {renderSubDetail("Bias Details (Full ML)", (result as DeepAnalysisResult).detailed_sub_analyses?.bias, <EyeOff />)}
                {(result as DeepAnalysisResult).detailed_sub_analyses?.patterns && renderSubDetail("Pattern Details (Full)", (result as DeepAnalysisResult).detailed_sub_analyses?.patterns, <Newspaper />)}
                {(result as DeepAnalysisResult).detailed_sub_analyses?.lightweight_nigerian_bias && renderSubDetail("Lightweight Nigerian Bias (Full)", (result as DeepAnalysisResult).detailed_sub_analyses?.lightweight_nigerian_bias, <Sparkles />)}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
