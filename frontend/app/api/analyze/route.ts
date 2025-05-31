import { type NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase"; // For saving to DB

// Keep or adjust AnalysisResult interface as needed based on Python output
interface AnalysisResult {
  trust_score: number; // Adjusted to match Python output (snake_case)
  indicator: string; // Adjusted to match Python output (sentiment -> indicator)
  primary_bias_type: string; // Adjusted to match Python output
  explanation: string[]; // Adjusted to match Python output (can be string[])
  tip: string; // Adjusted to match Python output (summary -> tip)
  // metadata: object; // Python also returns a metadata object, ensure it's handled or defined if needed
  // Fields like emotionalLanguage, misinformationFlag are part of detailed_sub_analyses or calculated differently now.
  // The client-side AnalysisResult might need further adaptation based on what Python's `analyze` returns.
  // For now, this reflects the primary fields from Python's `final_result`.
  // Let's assume the python `analyze` function returns these keys directly or they are mapped before this point.
  // If Python returns 'sentiment' and 'biasType', the interface should reflect that.
  // Based on biaslens/analyzer.py, the main 'analyze' returns:
  // 'trust_score', 'indicator', 'explanation', 'tip', 'primary_bias_type', 'metadata'
  // 'emotionalLanguage' and 'misinformationFlag' are not top-level keys in the final_result.
  // They are within detailed_sub_analyses or pattern_result.
  // For Supabase, we need to map them correctly.
}

// Interface for what Supabase expects/returns, which might be different from Python's raw output
interface DbAnalysisRecord {
  id: string;
  user_id: string;
  original_text: string;
  trust_score: number;
  sentiment: string; // This is 'indicator' from Python
  bias_type: string; // This is 'primary_bias_type' from Python
  emotional_language: string[]; // This needs to be sourced if required
  misinformation_flag: boolean; // This needs to be sourced if required
  explanation: string; // Python 'explanation' is string[]
  ai_summary: string; // This is 'tip' from Python
  created_at: string;
}


export async function POST(request: NextRequest) {
  try {
    const { text, userId } = await request.json();

    if (!text || !userId) {
      return NextResponse.json(
        { error: "Text and user ID are required" },
        { status: 400 }
      );
    }

    const apiBaseUrl = process.env.VERCEL_URL
        ? `https://${process.env.VERCEL_URL}`
        : process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

    const pythonApiUrl = `${apiBaseUrl}/api/analyze`;

    console.log(`[Next.js API /api/analyze] Attempting to fetch: ${pythonApiUrl}`);
    console.log(`[Next.js API /api/analyze] Request body for Python: ${JSON.stringify({ text: text })}`);

    const pythonResponse = await fetch(pythonApiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: text }),
    });

    if (!pythonResponse.ok) {
      const errorData = await pythonResponse.json();
      console.error("Python API error (analyze):", errorData);
      console.error(`[Next.js API /api/analyze] Python API response status: ${pythonResponse.status}`);
      throw new Error(errorData.error || "Analysis by Python script failed");
    }

    // Assuming pythonResponse.json() directly matches the expected structure from Python's analyze
    // Keys from python: 'trust_score', 'indicator', 'explanation', 'tip', 'primary_bias_type', 'metadata'
    const analysisFromPython = await pythonResponse.json();

    // Map Python output to the fields expected by Supabase
    // This requires careful mapping based on what `biaslens/analyzer.py` actually returns
    // and what the database schema expects.
    const supabasePayload = {
      user_id: userId,
      original_text: text,
      trust_score: analysisFromPython.trust_score,
      sentiment: analysisFromPython.indicator, // Map 'indicator' to 'sentiment' for DB
      bias_type: analysisFromPython.primary_bias_type, // Map 'primary_bias_type' to 'bias_type'
      // emotional_language and misinformation_flag are not directly in python's final_result top level.
      // They would need to be extracted from `detailed_sub_analyses` if that was included,
      // or handled differently. For now, let's use placeholders or assume they are not critical for DB.
      emotional_language: analysisFromPython.metadata?.detailed_sub_analyses?.emotion?.keywords || [], // Example placeholder
      misinformation_flag: analysisFromPython.metadata?.detailed_sub_analyses?.patterns?.fake_news?.detected || false, // Example placeholder
      explanation: Array.isArray(analysisFromPython.explanation) ? analysisFromPython.explanation.join('\n') : analysisFromPython.explanation,
      ai_summary: analysisFromPython.tip, // Map 'tip' to 'ai_summary'
    };

    const supabase = createServerClient();
    const { data: dbData, error: dbError } = await supabase
      .from("analysis_history")
      .insert(supabasePayload)
      .select()
      .single();

    if (dbError) {
      console.error("Database error:", dbError);
      // Log more details for debugging
      console.error("Supabase payload:", supabasePayload);
      console.error("Python analysis result for DB insertion:", analysisFromPython);
      return NextResponse.json(
        { error: `Failed to save analysis: ${dbError.message}` },
        { status: 500 }
      );
    }

    // Construct the final response to the client
    // It should match what the client-side `AnalysisResult` interface expects (on AnalyzePage.tsx)
    // Client `AnalysisResult`: id, trustScore, sentiment, biasType, emotionalLanguage, misinformationFlag, explanation, summary, createdAt
    const clientResponse: {
      id: string;
      trustScore: number;
      sentiment: string;
      biasType: string;
      emotionalLanguage: string[];
      misinformationFlag: boolean;
      explanation: string;
      summary: string;
      createdAt: string;
    } = {
      id: dbData.id,
      trustScore: dbData.trust_score,
      sentiment: dbData.sentiment,
      biasType: dbData.bias_type,
      emotionalLanguage: dbData.emotional_language,
      misinformationFlag: dbData.misinformation_flag,
      explanation: dbData.explanation,
      summary: dbData.ai_summary,
      createdAt: dbData.created_at,
    };

    return NextResponse.json(clientResponse);

  } catch (error) {
    console.error("Main analysis endpoint error:", error);
    console.error(`[Next.js API /api/analyze] Error in POST handler:`, error);
    let errorMessage = "Failed to analyze text";
    if (error instanceof Error) {
        errorMessage = error.message;
    }
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}
