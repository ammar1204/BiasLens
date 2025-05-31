import { type NextRequest, NextResponse } from "next/server";

// Keep or adjust QuickAnalysisResult interface
// This should match what Python Flask app /api/quick_analyze returns
// Python's quick_analyze returns: 'score', 'indicator', 'explanation', 'tip'
interface QuickAnalysisResult {
  score?: number;
  indicator?: string;
  explanation?: string[] | string; // Python's quick_analyze returns a list of strings for explanation
  tip?: string;
}

export async function POST(request: NextRequest) {
  try {
    const { text } = await request.json(); // userId not strictly needed if not saving

    if (!text || typeof text !== "string") {
      return NextResponse.json(
        { error: "Invalid input: text is required and must be a string." },
        { status: 400 }
      );
    }

    const apiBaseUrl = process.env.VERCEL_URL
        ? `https://${process.env.VERCEL_URL}`
        : process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

    const pythonApiUrl = `${apiBaseUrl}/api/quick_analyze`;

    console.log(`[Next.js API /api/quick_analyze] Attempting to fetch: ${pythonApiUrl}`);
    console.log(`[Next.js API /api/quick_analyze] Request body for Python: ${JSON.stringify({ text: text })}`);

    const pythonResponse = await fetch(pythonApiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: text }),
    });

    if (!pythonResponse.ok) {
      const errorData = await pythonResponse.json();
      console.error("Python API error (quick_analyze):", errorData);
      console.error(`[Next.js API /api/quick_analyze] Python API response status: ${pythonResponse.status}`);
      throw new Error(errorData.error || "Quick analysis by Python script failed");
    }

    const analysisResult: QuickAnalysisResult = await pythonResponse.json();

    // The client-side mapping in AnalyzePage.tsx for quick_analyze expects:
    // quickResult.score -> trustScore
    // quickResult.indicator -> sentiment
    // quickResult.explanation -> explanation (string)
    // quickResult.tip -> summary
    // The Python script already returns these keys, so no explicit mapping is needed here.
    // The structure of QuickAnalysisResult interface here should match the Python output directly.
    return NextResponse.json(analysisResult);

  } catch (error) {
    console.error("Quick analysis endpoint error:", error);
    console.error(`[Next.js API /api/quick_analyze] Error in POST handler:`, error);
    let errorMessage = "Failed to perform quick analysis.";
    if (error instanceof Error) {
        errorMessage = error.message;
    }
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}
