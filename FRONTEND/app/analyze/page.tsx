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

interface AnalysisResult {
  id: string
  trustScore: number
  sentiment: string
  biasType: string
  emotionalLanguage: string[]
  misinformationFlag: boolean
  explanation: string
  summary: string
  createdAt: string
}

export default function AnalyzePage() {
  const { user, loading } = useAuth()
  const [text, setText] = useState("")
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const { toast } = useToast()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/signin")
    }
  }, [user, loading, router])

  const handleAnalyze = async () => {
    if (!text.trim()) {
      toast({
        title: "Error",
        description: "Please enter some text to analyze",
        variant: "destructive",
      })
      return
    }

    setAnalyzing(true)
    setResult(null)

    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
      const response = await fetch(`${apiBaseUrl}/quick_analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: text.trim(),
          userId: user?.id,
        }),
      })

      if (!response.ok) {
        throw new Error("Analysis failed")
      }

      const analysisResult = await response.json()
      setResult(analysisResult)

      toast({
        title: "Analysis Complete",
        description: "Your text has been analyzed successfully!",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to analyze text. Please try again.",
        variant: "destructive",
      })
    } finally {
      setAnalyzing(false)
    }
  }

  const handleDeepAnalyze = async () => {
    if (!text.trim()) {
      toast({
        title: "Error",
        description: "Please enter some text to analyze",
        variant: "destructive",
      })
      return
    }

    setAnalyzing(true)
    setResult(null)

    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
      const response = await fetch(`${apiBaseUrl}/analyze`, { // Changed endpoint and use env var
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: text.trim(),
          userId: user?.id,
        }),
      })

      if (!response.ok) {
        throw new Error("Deep analysis failed")
      }

      const analysisResult = await response.json()
      setResult(analysisResult)

      toast({
        title: "Deep Analysis Complete",
        description: "Your text has been deeply analyzed successfully!",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to deeply analyze text. Please try again.",
        variant: "destructive",
      })
    } finally {
      setAnalyzing(false)
    }
  }

  const getTrustScoreColor = (score: number) => {
    if (score >= 70) return "text-green-600"
    if (score >= 40) return "text-yellow-600"
    return "text-red-600"
  }

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case "positive":
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case "negative":
        return <XCircle className="h-5 w-5 text-red-600" />
      default:
        return <MessageSquare className="h-5 w-5 text-gray-600" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="text-center mb-8">
        <h1 className="text-3xl md:text-4xl font-bold mb-4">Analyze Text for Bias</h1>
        <p className="text-lg text-muted-foreground">
          Paste any article, social media post, or news content to get instant AI-powered analysis
        </p>
      </div>

      {/* Input Section */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Text Analysis
          </CardTitle>
          <CardDescription>Enter the text you want to analyze for bias, sentiment, and misinformation</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            placeholder="Paste your text here... (articles, social media posts, news content, etc.)"
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="min-h-[200px]"
            maxLength={5000}
          />
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">{text.length}/5000 characters</span>
            <Button onClick={handleAnalyze} disabled={analyzing || !text.trim()} size="lg">
              {analyzing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {analyzing ? "Analyzing..." : "Quick Analysis"}
            </Button>
             <Button onClick={handleDeepAnalyze} disabled={analyzing || !text.trim()} size="lg">
              {analyzing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {analyzing ? "Analyzing..." : "Deep Analysis"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results Section */}
      {result && (
        <div className="space-y-6">
          {/* Trust Score */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Trust Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold">
                    <span className={getTrustScoreColor(result.trustScore)}>{result.trustScore}%</span>
                  </span>
                  <Badge
                    variant={
                      result.trustScore >= 70 ? "default" : result.trustScore >= 40 ? "secondary" : "destructive"
                    }
                  >
                    {result.trustScore >= 70 ? "Trustworthy" : result.trustScore >= 40 ? "Moderate" : "Low Trust"}
                  </Badge>
                </div>
                <Progress value={result.trustScore} className="h-3" />
              </div>
            </CardContent>
          </Card>

          {/* Analysis Details */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Sentiment & Bias */}
            <Card>
              <CardHeader>
                <CardTitle>Sentiment & Bias</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Sentiment:</span>
                  <div className="flex items-center gap-2">
                    {getSentimentIcon(result.sentiment)}
                    <Badge variant="outline" className="capitalize">
                      {result.sentiment}
                    </Badge>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium">Bias Type:</span>
                  <Badge variant={result.biasType === "none" ? "default" : "secondary"}>
                    {result.biasType === "none" ? "No Bias Detected" : result.biasType}
                  </Badge>
                </div>
                {result.misinformationFlag && (
                  <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-red-600" />
                    <span className="text-sm font-medium text-red-800 dark:text-red-200">
                      Potential Misinformation Detected
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Emotional Language */}
            <Card>
              <CardHeader>
                <CardTitle>Emotional Language</CardTitle>
              </CardHeader>
              <CardContent>
                {result.emotionalLanguage.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {result.emotionalLanguage.map((phrase, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        "{phrase}"
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No emotional language detected</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Explanation */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground leading-relaxed">{result.explanation}</p>
            </CardContent>
          </Card>

          {/* AI Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Objective Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground leading-relaxed">{result.summary}</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
