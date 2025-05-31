import { type NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
// No Supabase client needed here if quick_analyze doesn't save to DB.
// If it does, or might in the future, you can add:
// import { createServerClient } from "@/lib/supabase";

// Define the expected structure for the quick analysis result.
// This should match what your Python script's quick_analyze function returns.
interface QuickAnalysisResult {
  score?: number; // Making fields optional in case of error or different structure
  indicator?: string;
  explanation?: string[] | string; // Can be an array or single string
  tip?: string;
  // Add other fields if your quick_analyze Python function returns more
}

export async function POST(request: NextRequest) {
  try {
    const { text, userId } = await request.json(); // Assuming userId might be used later

    if (!text || typeof text !== "string") {
      return NextResponse.json(
        { error: "Invalid input: text is required and must be a string." },
        { status: 400 }
      );
    }
    // userId validation can be added if it becomes mandatory for this endpoint

    const projectRoot = process.cwd();
    const scriptPath = path.join(projectRoot, "biaslens", "analyzer.py");
    const pythonExecutable = "python3"; // Or "python"

    const analysis = await new Promise<QuickAnalysisResult>((resolve, reject) => {
      const pythonProcess = spawn(pythonExecutable, [
        scriptPath,
        "quick_analyze", // Specify the function to call
        text,
      ]);

      let stdoutData = "";
      let stderrData = "";

      pythonProcess.stdout.on("data", (data) => {
        stdoutData += data.toString();
      });

      pythonProcess.stderr.on("data", (data) => {
        stderrData += data.toString();
      });

      pythonProcess.on("close", (code) => {
        if (code === 0) {
          try {
            // Trim stdoutData to remove potential trailing newlines from Python's print
            const result = JSON.parse(stdoutData.trim());
            resolve(result);
          } catch (parseError) {
            console.error("JSON parsing error in quick_analyze:", parseError);
            console.error("Python stdout (quick_analyze):", stdoutData);
            console.error("Python stderr (quick_analyze):", stderrData);
            reject(new Error("Failed to parse Python script output for quick analysis."));
          }
        } else {
          console.error(`Python script (quick_analyze) exited with code ${code}`);
          console.error("Python stderr (quick_analyze):", stderrData);
          console.error("Python stdout (quick_analyze):", stdoutData);
          reject(new Error(`Python script error (quick_analyze): ${stderrData || "Unknown error"}`));
        }
      });

      pythonProcess.on("error", (error) => {
        console.error("Failed to start Python process (quick_analyze):", error);
        if ((error as any).code === 'ENOENT') {
          reject(new Error(`Python executable (${pythonExecutable}) not found. Please ensure Python is installed and in PATH.`));
        } else {
          reject(new Error("Failed to start Python script for quick analysis."));
        }
      });
    });

    // Unlike the main 'analyze' endpoint, quick_analyze results are typically not saved to the database.
    // If you need to save them, you would add Supabase client initialization and insert logic here.
    // For example:
    // const supabase = createServerClient();
    // const { error: dbError } = await supabase.from("quick_analysis_log").insert({ ... });
    // if (dbError) { /* handle error */ }

    return NextResponse.json(analysis);
  } catch (error) {
    console.error("Quick analysis endpoint error:", error);
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
