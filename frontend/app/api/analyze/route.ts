import { type NextRequest, NextResponse } from "next/server"
import { generateText } from "ai"
import { openai } from "@ai-sdk/openai"
import { createServerClient } from "@/lib/supabase"

export async function POST(request: NextRequest) {
  try {
    const { text, userId } = await request.json()

    if (!text || !userId) {
      return NextResponse.json({ error: "Text and user ID are required" }, { status: 400 })
    }

    // AI Analysis using OpenAI
    const { text: analysisResult } = await generateText({
      model: openai("gpt-4o"),
      system: `You are BiaLens, an expert AI system that analyzes text for bias, sentiment, and misinformation. 

Analyze the provided text and return a JSON response with the following structure:
{
  "trustScore": number (0-100),
  "sentiment": "positive" | "negative" | "neutral",
  "biasType": string (e.g., "political", "racial", "gender", "none"),
  "emotionalLanguage": string[] (array of detected emotional phrases),
  "misinformationFlag": boolean,
  "explanation": string (detailed explanation of findings),
  "summary": string (objective summary of the text)
}

Guidelines:
- Trust score should be lower for highly biased, emotional, or potentially misleading content
- Identify specific emotional language and loaded phrases
- Flag potential misinformation based on unsubstantiated claims, conspiracy theories, or manipulative language
- Provide clear, educational explanations
- Keep the summary objective and factual`,
      prompt: `Analyze this text for bias, sentiment, and misinformation:\n\n"${text}"`,
    })

    let analysis
    try {
      analysis = JSON.parse(analysisResult)
    } catch (parseError) {
      // Fallback if JSON parsing fails
      analysis = {
        trustScore: 50,
        sentiment: "neutral",
        biasType: "unknown",
        emotionalLanguage: [],
        misinformationFlag: false,
        explanation: "Analysis completed but formatting error occurred.",
        summary: text.substring(0, 200) + "...",
      }
    }

    // Save to database
    const supabase = createServerClient()
    const { data, error } = await supabase
      .from("analysis_history")
      .insert({
        user_id: userId,
        original_text: text,
        trust_score: analysis.trustScore,
        sentiment: analysis.sentiment,
        bias_type: analysis.biasType,
        emotional_language: analysis.emotionalLanguage,
        misinformation_flag: analysis.misinformationFlag,
        explanation: analysis.explanation,
        ai_summary: analysis.summary,
      })
      .select()
      .single()

    if (error) {
      console.error("Database error:", error)
      return NextResponse.json({ error: "Failed to save analysis" }, { status: 500 })
    }

    return NextResponse.json({
      id: data.id,
      ...analysis,
      createdAt: data.created_at,
    })
  } catch (error) {
    console.error("Analysis error:", error)
    return NextResponse.json({ error: "Failed to analyze text" }, { status: 500 })
  }
}
