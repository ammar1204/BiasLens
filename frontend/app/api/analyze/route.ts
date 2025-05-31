import { type NextRequest, NextResponse } from "next/server"
import { spawn } from "child_process"
import path from "path"
import { createServerClient } from "@/lib/supabase"

// Define the expected structure of the analysis result from the Python script
interface AnalysisResult {
  trustScore: number
  sentiment: "positive" | "negative" | "neutral"
  biasType: string
  emotionalLanguage: string[]
  misinformationFlag: boolean
  explanation: string
  summary: string
  // Add any other fields that your Python script might return
  // and are expected by the database or frontend.
  // For example, if the Python script returns the 'indicator' or 'tip'
  // from the quick_analyze example, you might want them here.
}


export async function POST(request: NextRequest) {
  try {
    const { text, userId } = await request.json()

    if (!text || !userId) {
      return NextResponse.json({ error: "Text and user ID are required" }, { status: 400 })
    }

    // Path to the Python script - ensure this is correct
    // __dirname in ES modules for server components might be tricky.
    // Using process.cwd() and then constructing path might be more reliable for Next.js server routes.
    // The script is in biaslens/analyzer.py, relative to the root of the project.
    // Current file: frontend/app/api/analyze/route.ts
    // process.cwd() should be the project root.
    const projectRoot = process.cwd()
    const scriptPath = path.join(projectRoot, "biaslens", "analyzer.py")
    // Alternative if analyzer.py is not directly executable with text arg:
    // const scriptPath = path.join(projectRoot, "biaslens", "cli_runner.py");


    const analysis = await new Promise<AnalysisResult>((resolve, reject) => {
      // Try 'python3' first, then 'python' if 'python3' is not found or fails.
      // For simplicity, we'll try python3 here. Robust checking might be needed.
      const pythonExecutable = "python3" // Or "python" as a fallback

      // Ensure analyzer.py is executable and accepts text as a command line argument,
      // and prints JSON to stdout.
      const pythonProcess = spawn(pythonExecutable, [scriptPath, text])

      let stdoutData = ""
      let stderrData = ""

      pythonProcess.stdout.on("data", (data) => {
        stdoutData += data.toString()
      })

      pythonProcess.stderr.on("data", (data) => {
        stderrData += data.toString()
      })

      pythonProcess.on("close", (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdoutData)
            resolve(result)
          } catch (parseError) {
            console.error("JSON parsing error:", parseError)
            console.error("Python stdout:", stdoutData)
            console.error("Python stderr:", stderrData)
            reject(new Error("Failed to parse Python script output."))
          }
        } else {
          console.error(`Python script exited with code ${code}`)
          console.error("Python stderr:", stderrData)
          console.error("Python stdout:", stdoutData) // Also log stdout in case of error
          reject(new Error(`Python script error: ${stderrData || "Unknown error"}`))
        }
      })

      pythonProcess.on("error", (error) => {
        console.error("Failed to start Python process:", error)
        if ((error as any).code === 'ENOENT') {
          reject(new Error(`Python executable (${pythonExecutable}) not found. Please ensure Python is installed and in PATH.`))
        } else {
          reject(new Error("Failed to start Python script."))
        }
      })
    })

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
