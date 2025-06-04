"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Loader2, AlertTriangle, CheckCircle, XCircle, Brain, TrendingUp, MessageSquare, Info, Zap, EyeOff, Newspaper, Lightbulb, Gauge, Palette, Fingerprint, Sparkles, ShieldCheck, BarChart3, SearchCheck } from "lucide-react"; // Added more icons
import { useToast } from "@/hooks/use-toast";
import { useRouter } from "next/navigation";

// --- TypeScript Interfaces for API Responses ---

// --- "Quick" Analysis Interfaces ---
interface QuickToneAnalysisModel {
  sentiment_label?: string | null;
  sentiment_confidence?: number | null;
}

// LightweightNigerianBiasAssessmentModel is reused for bias_analysis in QuickAnalysisResult

interface QuickManipulationAnalysisModel {
  is_clickbait?: boolean | null;
}

interface QuickVeracitySignalsModel {
  fake_news_risk_level?: string | null;
  matched_suspicious_phrases?: string[] | null;
}

interface QuickAnalysisResult {
  score: number | null;
  indicator: string | null;
  explanation: string | null;
  tip: string | null;
  // New structured fields for quick_analyze
  tone_analysis?: QuickToneAnalysisModel | null;
  bias_analysis?: LightweightNigerianBiasAssessmentModel | null; // Reusing this existing detailed model
  manipulation_analysis?: QuickManipulationAnalysisModel | null;
  veracity_signals?: QuickVeracitySignalsModel | null;
}


// --- "Core Solution" Interfaces for Deep Analysis (/analyze endpoint) ---
interface ToneAnalysisModel { // For Deep Analysis
  primary_tone?: string | null;
  is_emotionally_charged?: boolean | null;
  emotional_manipulation_risk?: string | null;
  sentiment_label?: string | null;
  sentiment_confidence?: number | null;
}

interface BiasAnalysisModel { // For Deep Analysis
  primary_bias_type?: string | null;
  bias_strength_label?: string | null;
  ml_model_confidence?: number | null;
  source_of_primary_bias?: string | null;
}

interface ManipulationAnalysisModel { // For Deep Analysis
  is_clickbait?: boolean | null;
  engagement_bait_score?: number | null;
  sensationalism_score?: number | null;
}

interface VeracitySignalsModel { // For Deep Analysis
  fake_news_risk_level?: string | null;
  matched_suspicious_phrases?: string[] | null;
}

interface LightweightNigerianBiasAssessmentModel {
  inferred_bias_type?: string | null;
  bias_category?: string | null;
  bias_target?: string | null;
  matched_keywords?: string[] | null;
}

// Interfaces for the content of `detailed_sub_analyses` (original full structures)
interface SentimentDetail {
  label: string;
  confidence: number;
  all_scores?: { negative?: number; neutral?: number; positive?: number; };
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

// Main interface for Deep Analysis results - "Core Solution" Structure
interface DeepAnalysisResult {
  trust_score: number | null;
  indicator: string | null;
  explanation: string[] | null;
  tip: string | null;

  tone_analysis?: ToneAnalysisModel | null;
  bias_analysis?: BiasAnalysisModel | null;
  manipulation_analysis?: ManipulationAnalysisModel | null;
  veracity_signals?: VeracitySignalsModel | null;

  lightweight_nigerian_bias_assessment?: LightweightNigerianBiasAssessmentModel | null;

  detailed_sub_analyses?: DetailedSubAnalysesResult | null;
}

type AnalysisResultType = QuickAnalysisResult | DeepAnalysisResult | null;
type AnalysisMode = "quick" | "deep" | null;

// readableKeyMap should be defined outside the component if it doesn't need access to component's state/props
// or inside if it does, or passed as a prop. For this case, outside is fine.
const readableKeyMap: Record<string, string> = {
  // Common keys from various analysis sections
  is_biased: "Is Biased:",
  bias_level: "Bias Level:",
  bias_strength_label: "Bias Strength:",
  primary_bias_type: "Primary Bias Type:",
  source_of_primary_bias: "Source of Primary Bias:",
  is_clickbait: "Clickbait Detected:",
  engagement_bait_score: "Engagement Bait Level:",
  sensationalism_score: "Sensationalism Level:",
  fake_news_risk_level: "Fake News Risk Level:",
  matched_suspicious_phrases: "Matched Suspicious Phrases:",
  primary_tone: "Primary Tone:",
  is_emotionally_charged: "Emotionally Charged:",
  emotional_manipulation_risk: "Emotional Manipulation Risk:",
  sentiment_label: "Sentiment:",
  inferred_bias_type: "Inferred Bias Type (Pattern-based):",
  bias_category: "Bias Category (Pattern-based):",
  bias_target: "Bias Target (Pattern-based):",
  matched_keywords: "Matched Keywords (Pattern-based):",
  has_triggers: "Has Triggers:",
  trigger_matches: "Trigger Matches:",
  clickbait_matches: "Clickbait Matches:",
  total_flags: "Total Flags:",
  fake_matches: "Matched Fake News Phrases:", // For FakeNewsDetail
  credibility_flags: "Credibility Red Flags:",
  credibility_score: "Credibility Score:",
  has_viral_patterns: "Has Viral Patterns:",
  viral_matches: "Viral Matches:",
  manipulation_level: "Manipulation Level:",
  // Keys from BiasDetection objects within nigerian_detections
  term: "Term:",
  category: "Category:",
  // bias_level: "Bias Level:", // Already defined
  context: "Context:",
  direction: "Direction:",
  explanation: "Explanation:",
  // Keys from specific_detections (which are BiasDetection like)
  // term, category, bias_level, confidence, direction, explanation, context are covered
  // Keys from type_analysis in BiasDetail
  type: "Type:", // Generic, might need context if used elsewhere for different things
  // confidence: "Confidence:", // Already defined
  nigerian_context: "Nigerian Context Specific:",
  // Keys from overall_bias
  // is_biased, confidence, level (covered by bias_level)
  // Keys from bias_details (NewBiasLensAnalyzer)
  // type, type_confidence, nigerian_context, specific_detections (handled by deeper rendering later)
  // Keys from clickbait (NewBiasLensAnalyzer)
  // is_clickbait, confidence, level, detected_patterns, explanation
  detected_patterns: "Detected Clickbait Patterns:",
  // Keys from technical_details (NewBiasLensAnalyzer)
  // explanation: "Technical Explanation:", // Can conflict with other 'explanation' keys
  error: "Error:",
  // For detailed sub-analyses raw fields
  flag: "Flagged:",
  detected: "Detected:",
  headline_comparison: "Headline Comparison:",
  trigger_details: "Trigger Details:",
  clickbait_details: "Clickbait Details:",
  details: "Details:", // Generic for FakeNewsDetail.details
  level: "Level:", // Generic, e.g. for clickbait level from NewBiasLensAnalyzer
  specific_detections: "Specific Detections:"
};

export default function AnalyzePage() {
  const { user, loading: authLoading } = useAuth()
  const [text, setText] = useState("")
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<AnalysisResultType>(null)
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const { toast } = useToast()
  const router = useRouter()

  // Helper function to render individual field values based on their type
  // This function is defined inside AnalyzePage to have access to readableKeyMap if it were state or prop based.
  // Since readableKeyMap is global const in this file, renderFieldValue could also be global.
  // Keeping it here for now as it's closely tied to this component's rendering logic.
  const renderFieldValue = (originalKey: string, value: any, isNested: boolean = false): React.ReactNode => {
    // Keys to explicitly ignore
    const keysToIgnore: string[] = [
      "ml_model_confidence",
      "sentiment_confidence",
      "confidence", // Exact match for 'confidence'
      "base_model_score",
      "all_scores",
      "trigger_score",
      "clickbait_score",
      "fake_score",
      "viral_score",
      "raw_new_analyzer_result",
      "count",
      "categories_present",
      "has_specific_nigerian_bias",
      // The following are now relabeled in readableKeyMap, but if the raw key is still used, ignore.
      // "engagement_bait_score", // This is now "Engagement Bait Level"
      // "sensationalism_score" // This is now "Sensationalism Level"
    ];

    if (keysToIgnore.includes(originalKey)) {
      return null;
    }

    if (value === null || value === undefined) return null;
    // Avoid rendering the 'error' key if it's already handled or if its value suggests no error.
    // This check might need refinement based on how 'error' fields are structured and used.
    if (originalKey === 'error' && (typeof value === 'string' && value.toLowerCase().includes("no error") || !value )) return null;


    const displayKey = readableKeyMap[originalKey] || originalKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    const displayKeyComponent = <span className="font-semibold">{displayKey}</span>;

    const baseKeyClass = isNested ? "text-xs" : "text-sm";

    if (typeof value === 'boolean') {
      return <div key={originalKey} className={baseKeyClass}>{displayKeyComponent} {value ? "Yes" : "No"}</div>;
    }
    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <div key={originalKey} className={baseKeyClass}>{displayKeyComponent} N/A</div>;
      }
      if (value.every(item => typeof item === 'string')) {
        return (
          <div key={originalKey} className={baseKeyClass}>
            {displayKeyComponent}
            <ul className="list-disc list-inside pl-4 mt-1 space-y-0.5">
              {value.map((item, index) => <li key={index}>{item}</li>)}
            </ul>
          </div>
        );
      } else if (value.every(item => typeof item === 'object' && item !== null)) {
        return (
          <div key={originalKey} className={baseKeyClass}>
            {displayKeyComponent}
            <div className={`pl-2 mt-1 space-y-2 ${isNested ? "border-l-2 border-slate-200 dark:border-slate-700 ml-2 pl-2" : ""}`}>
              {value.map((item, index) => (
                <div key={index} className={`p-2 rounded ${isNested ? "bg-muted/30 dark:bg-muted/80" : "bg-muted/50 dark:bg-muted/70 border dark:border-slate-700"} `}>
                  <div className="space-y-1">
                     {Object.entries(item).map(([objKey, objValue]) => renderFieldValue(objKey, objValue, true))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      } else { // Fallback for mixed arrays or other non-string, non-object arrays
        return <div key={originalKey} className={`${baseKeyClass} break-all`}>{displayKeyComponent} <pre className="whitespace-pre-wrap text-xs bg-muted p-2 rounded mt-1">{JSON.stringify(value, null, 2)}</pre></div>;
      }
    }
    if (typeof value === 'object' && value !== null) {
      if (originalKey === 'raw_new_analyzer_result' && !isNested) {
        return <div key={originalKey} className={baseKeyClass}>{displayKeyComponent} <span className="text-muted-foreground text-xs">(Full raw data from the new bias analyzer - hidden for brevity)</span></div>;
      }
      const objEntries = Object.entries(value).filter(([_, val]) => val !== null && val !== undefined);
      if (objEntries.length === 0) return <div key={originalKey} className={baseKeyClass}>{displayKeyComponent} Empty object</div>;

      return (
        <div key={originalKey} className={baseKeyClass}>
          {displayKeyComponent}
          <div className={`pl-2 mt-1 space-y-1 ${isNested ? "border-l-2 border-slate-200 dark:border-slate-700 ml-2 pl-2" : ""}`}>
            {objEntries.map(([objKey, objValue]) => renderFieldValue(objKey, objValue, true))}
          </div>
        </div>
      );
    }
    // Default for strings, numbers
    // Add specific check for error strings to style them
     if (originalKey === 'error' && typeof value === 'string') {
        return <div key={originalKey} className={`${baseKeyClass} text-red-500 dark:text-red-400`}>{displayKeyComponent} {String(value)}</div>;
    }
    return <div key={originalKey} className={baseKeyClass}>{displayKeyComponent} {String(value)}</div>;
  };

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
    setAnalyzing(true); setResult(null); setApiError(null); setAnalysisMode("quick");
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
      const response = await fetch(`${apiBaseUrl}/quick_analyze`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: text.trim() }),
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || responseData.error || "Quick analysis failed");
      setResult(responseData as QuickAnalysisResult);
      toast({ title: "Quick Analysis Complete", description: "Text analyzed successfully!" });
    } catch (error: any) {
      console.error("Quick Analysis API Error:", error);
      const errorMsg = error.message || "Failed to analyze text. Please try again.";
      setApiError(errorMsg); toast({ title: "Error", description: errorMsg, variant: "destructive" });
    } finally { setAnalyzing(false); }
  }

  const handleDeepAnalyze = async () => { // This is for Deep Analysis
    if (!text.trim()) {
      toast({ title: "Error", description: "Please enter some text to analyze", variant: "destructive" })
      return
    }
    setAnalyzing(true); setResult(null); setApiError(null); setAnalysisMode("deep");
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
      const requestBody = { text: text.trim(), include_detailed_results: true, include_patterns: true, };
      const response = await fetch(`${apiBaseUrl}/analyze`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(requestBody),
      });
      const responseData = await response.json();
      if (!response.ok) throw new Error(responseData.detail || responseData.error || "Deep analysis failed");
      setResult(responseData as DeepAnalysisResult);
      toast({ title: "Deep Analysis Complete", description: "Text deeply analyzed successfully!" });
    } catch (error: any) {
      console.error("Deep Analysis API Error:", error);
      const errorMsg = error.message || "Failed to deeply analyze text. Please try again.";
      setApiError(errorMsg); toast({ title: "Error", description: errorMsg, variant: "destructive" });
    } finally { setAnalyzing(false); }
  }

  const getTrustScoreColor = (score: number | null) => {
    if (score === null) return "text-gray-600";
    if (score >= 70) return "text-green-600";
    if (score >= 40) return "text-yellow-600";
    return "text-red-600";
  }

  // const getQualitativeAssessment = (score: number | null): string => {
  //   if (score === null) return "Assessment: Not Available";
  //   if (score >= 70) return "Assessment: Generally Trustworthy";
  //   if (score >= 40) return "Assessment: Use Caution";
  //   return "Assessment: Potential Issues Detected";
  // };

  const renderSubDetail = (title: string, data: any, icon?: React.ReactNode, cardDescription?: string) => {
    if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
        if (data && typeof data === 'object' && data.error && Object.keys(data).length === 1) {
             return ( <Card> <CardHeader><CardTitle className="flex items-center gap-2 text-base">{icon || <Info />} {title}</CardTitle>{cardDescription && <CardDescription>{cardDescription}</CardDescription>}</CardHeader> <CardContent><p className="text-sm text-red-500">{data.error}</p></CardContent> </Card> );
        }
        return ( <Card> <CardHeader><CardTitle className="flex items-center gap-2 text-base">{icon || <Info />} {title}</CardTitle>{cardDescription && <CardDescription>{cardDescription}</CardDescription>}</CardHeader> <CardContent><p className="text-sm text-muted-foreground">Data not available or not applicable for this item.</p></CardContent> </Card> );
    }
    const validEntries = Object.entries(data).filter(([_, value]) => value !== null && value !== undefined);
    if (validEntries.length === 0 || (validEntries.length === 1 && validEntries[0][0] === 'error' && validEntries[0][1] && typeof validEntries[0][1] === 'string' && validEntries[0][1].trim() !== '' && !validEntries[0][1].toLowerCase().includes("no error") )) {
         return ( <Card> <CardHeader><CardTitle className="flex items-center gap-2 text-base">{icon || <Info />} {title}</CardTitle>{cardDescription && <CardDescription>{cardDescription}</CardDescription>}</CardHeader> <CardContent><p className="text-sm text-muted-foreground">{ (validEntries.length === 1 && validEntries[0][0] === 'error' ? validEntries[0][1] : "Data not available or not applicable for this item.")}</p></CardContent> </Card> );
    }

    const renderedContent = validEntries
        .map(([key, value]) => renderFieldValue(key, value, false))
        .filter(item => item !== null);

    if (renderedContent.length === 0) {
        // If all fields were filtered out by renderFieldValue, treat as "Data not available"
        return ( <Card> <CardHeader><CardTitle className="flex items-center gap-2 text-base">{icon || <Info />} {title}</CardTitle>{cardDescription && <CardDescription>{cardDescription}</CardDescription>}</CardHeader> <CardContent><p className="text-sm text-muted-foreground">Data not available or not applicable for this item.</p></CardContent> </Card> );
    }

    return (
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2 text-base">{icon || <Info />} {title}</CardTitle>{cardDescription && <CardDescription>{cardDescription}</CardDescription>}</CardHeader>
        <CardContent className="space-y-2">
          {renderedContent}
        </CardContent>
      </Card>
    );
  };

  const renderCoreSolutionDetails = (res: DeepAnalysisResult) => { // For Deep Analysis
    if (!res.tone_analysis && !res.bias_analysis && !res.manipulation_analysis && !res.veracity_signals) {
      return null;
    }
    return (
      <>
        <h2 className="text-2xl font-semibold mt-8 mb-4 border-b pb-2">Key Analysis Insights</h2>
        <div className="grid md:grid-cols-2 gap-6">
          {res.tone_analysis && renderSubDetail("Tone & Sentiment", res.tone_analysis, <Palette />, "Overall emotional tone and sentiment perception.")}
          {res.bias_analysis && renderSubDetail("Bias Insights", res.bias_analysis, <EyeOff />, "Detected bias type, strength, and source.")}
          {res.manipulation_analysis && renderSubDetail("Manipulation Tactics", res.manipulation_analysis, <Fingerprint />, "Presence of clickbait or manipulative patterns.")}
          {res.veracity_signals && renderSubDetail("Veracity Signals", res.veracity_signals, <ShieldCheck />, "Indicators related to content reliability and authenticity.")}
        </div>
      </>
    )
  }

  const renderQuickAnalysisCoreDetails = (res: QuickAnalysisResult) => {
    if (!res.tone_analysis && !res.bias_analysis && !res.manipulation_analysis && !res.veracity_signals) {
      return null;
    }
    return (
      <>
        <h2 className="text-xl font-semibold mt-6 mb-3 border-b pb-1">Quick Insights Overview</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {res.tone_analysis && renderSubDetail("Quick Tone", res.tone_analysis, <MessageSquare />)}
          {/* Bias Analysis for Quick Mode uses LightweightNigerianBiasAssessmentModel directly */}
          {res.bias_analysis && (res.bias_analysis.inferred_bias_type && res.bias_analysis.inferred_bias_type !== "No specific patterns detected" && res.bias_analysis.inferred_bias_type !== "Nigerian context detected, specific bias type unclear from patterns") &&
            renderSubDetail("Quick Pattern Bias", res.bias_analysis, <Sparkles />)
          }
          {res.manipulation_analysis && renderSubDetail("Quick Manipulation", res.manipulation_analysis, <Fingerprint />)}
          {res.veracity_signals && renderSubDetail("Quick Veracity", res.veracity_signals, <SearchCheck />)}
        </div>
      </>
    )
  }

  if (authLoading) { return ( <div className="flex items-center justify-center min-h-screen"> <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div> </div> ) }
  if (!user) { return null }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="text-center mb-8"> <h1 className="text-3xl md:text-4xl font-bold mb-4">BiasLens Text Analyzer</h1> <p className="text-lg text-muted-foreground"> Paste text to analyze for bias, sentiment, emotional tone, and more. </p> </div>
      <Card className="mb-8 shadow-lg">
        <CardHeader> <CardTitle className="flex items-center gap-2 text-xl"> <Brain className="h-6 w-6 text-primary" /> Analyze Content </CardTitle> <CardDescription>Enter text (articles, posts, etc.) for AI-powered analysis.</CardDescription> </CardHeader>
        <CardContent className="space-y-4">
          <Textarea placeholder="Paste your text here..." value={text} onChange={(e) => setText(e.target.value)} className="min-h-[200px] text-base border-gray-300 focus:border-primary" maxLength={10000} />
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <span className="text-sm text-muted-foreground">{text.length}/10000 characters</span>
            <div className="flex gap-4"> <Button onClick={handleAnalyze} disabled={analyzing || !text.trim()} size="lg" variant="outline"> {analyzing && analysisMode === 'quick' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Quick Analysis </Button> <Button onClick={handleDeepAnalyze} disabled={analyzing || !text.trim()} size="lg"> {analyzing && analysisMode === 'deep' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Deep Analysis </Button> </div>
          </div>
        </CardContent>
      </Card>
      {apiError && ( <Card className="mb-8 bg-red-50 dark:bg-red-900 border-red-500 dark:border-red-700"> <CardHeader> <CardTitle className="flex items-center gap-2 text-red-700 dark:text-red-300"> <AlertTriangle /> Analysis Error </CardTitle> </CardHeader> <CardContent> <p className="text-red-600 dark:text-red-400">{apiError}</p> </CardContent> </Card> )}
      {result && !apiError && (
        <div className="space-y-6">
          <Card> {/* Overall Assessment Card */}
            <CardHeader> <CardTitle className="flex items-center gap-2"> <Gauge className="h-5 w-5 text-primary" /> Overall Assessment </CardTitle> </CardHeader>
            <CardContent className="space-y-4">
              {((analysisMode === 'deep' && (result as DeepAnalysisResult).trust_score !== null) || (analysisMode === 'quick' && (result as QuickAnalysisResult).score !== null)) ? (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold">
                      <span className={getTrustScoreColor(analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score)}>
                        {(analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score)}%
                      </span>
                      <span className="text-xl ml-1">Trust Score</span>
                    </span>
                    <Badge variant={ (((analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score) ?? 0) >= 70 ? "default" : (((analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score) ?? 0) >= 40 ? "secondary" : "destructive")) }> {result.indicator || "N/A"} </Badge>
                  </div>
                  <Progress value={(analysisMode === 'deep' ? (result as DeepAnalysisResult).trust_score : (result as QuickAnalysisResult).score)} className="h-3" />
                </>
              ) : <p className="text-muted-foreground">Trust score not available.</p>}
              <div className="mt-4"> <h4 className="font-semibold mb-1">Explanation:</h4> {Array.isArray(result.explanation) ? (result.explanation as string[]).map((line, index) => <p key={index} className="text-muted-foreground leading-relaxed">{line}</p>) : <p className="text-muted-foreground leading-relaxed">{result.explanation || "No explanation provided."}</p> } </div>
              <div className="mt-4"> <h4 className="font-semibold mb-1">Tip:</h4> <p className="text-muted-foreground leading-relaxed flex items-start gap-2"> <Lightbulb className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-1" /> <span>{result.tip || "No specific tip provided."}</span> </p> </div>
            </CardContent>
          </Card>

          {/* Render "Core Solution" details for Deep Analysis */}
          {analysisMode === 'deep' && renderCoreSolutionDetails(result as DeepAnalysisResult)}

          {/* Render "Core Solution" details for Quick Analysis */}
          {analysisMode === 'quick' && renderQuickAnalysisCoreDetails(result as QuickAnalysisResult)}

          {/* Display LightweightNigerianBiasAssessment for Deep Analysis (if not covered by quick's bias_analysis)
              Note: Quick mode's bias_analysis IS the LightweightNigerianBiasAssessment.
              For Deep mode, it's a separate top-level field if patterns are included.
          */}
          {analysisMode === 'deep' && (result as DeepAnalysisResult).lightweight_nigerian_bias_assessment?.inferred_bias_type &&
            (result as DeepAnalysisResult).lightweight_nigerian_bias_assessment?.inferred_bias_type !== "No specific patterns detected" &&
            (result as DeepAnalysisResult).lightweight_nigerian_bias_assessment?.inferred_bias_type !== "Nigerian context detected, specific bias type unclear from patterns" &&
          (
            <Card>
              <CardHeader> <CardTitle className="flex items-center gap-2"> <Sparkles className="h-5 w-5 text-purple-500" /> Lightweight Nigerian Bias Assessment </CardTitle> <CardDescription>Rule-based detection of Nigerian-specific bias patterns.</CardDescription> </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div><span className="font-semibold">Inferred Bias Type:</span> {(result as DeepAnalysisResult).lightweight_nigerian_bias_assessment!.inferred_bias_type}</div>
                {(result as DeepAnalysisResult).lightweight_nigerian_bias_assessment!.bias_category && <div><span className="font-semibold">Category:</span> <Badge variant="outline">{(result as DeepAnalysisResult).lightweight_nigerian_bias_assessment!.bias_category}</Badge></div>}
                {(result as DeepAnalysisResult).lightweight_nigerian_bias_assessment!.bias_target && <div><span className="font-semibold">Target:</span> <Badge variant="outline">{(result as DeepAnalysisResult).lightweight_nigerian_bias_assessment!.bias_target}</Badge></div>}
                {(result as DeepAnalysisResult).lightweight_nigerian_bias_assessment!.matched_keywords && (result as DeepAnalysisResult).lightweight_nigerian_bias_assessment!.matched_keywords!.length > 0 && (
                  <div> <span className="font-semibold">Matched Keywords:</span> <div className="flex flex-wrap gap-1 mt-1"> {(result as DeepAnalysisResult).lightweight_nigerian_bias_assessment!.matched_keywords!.map(keyword => ( <Badge key={keyword} variant="secondary" className="text-xs">{keyword}</Badge> ))} </div> </div>
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
