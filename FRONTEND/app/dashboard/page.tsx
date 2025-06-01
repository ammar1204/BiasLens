"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Calendar, TrendingUp, FileText, AlertTriangle, CheckCircle, XCircle, MessageSquare } from "lucide-react"
import { useRouter } from "next/navigation"
import { supabase } from "@/lib/supabase"
import { useToast } from "@/hooks/use-toast"

interface AnalysisHistory {
  id: string
  original_text: string
  trust_score: number
  sentiment: string
  bias_type: string
  emotional_language: string[]
  misinformation_flag: boolean
  explanation: string
  ai_summary: string
  created_at: string
}

export default function DashboardPage() {
  const { user, loading } = useAuth()
  const [analyses, setAnalyses] = useState<AnalysisHistory[]>([])
  const [loadingAnalyses, setLoadingAnalyses] = useState(true)
  const router = useRouter()
  const { toast } = useToast()

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/signin")
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      fetchAnalyses()
    }
  }, [user])

  const fetchAnalyses = async () => {
    try {
      const { data, error } = await supabase
        .from("analysis_history")
        .select("*")
        .eq("user_id", user?.id)
        .order("created_at", { ascending: false })

      if (error) throw error
      setAnalyses(data || [])
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load analysis history",
        variant: "destructive",
      })
    } finally {
      setLoadingAnalyses(false)
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
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "negative":
        return <XCircle className="h-4 w-4 text-red-600" />
      default:
        return <MessageSquare className="h-4 w-4 text-gray-600" />
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  if (loading || loadingAnalyses) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  const averageTrustScore =
    analyses.length > 0
      ? Math.round(analyses.reduce((sum, analysis) => sum + analysis.trust_score, 0) / analyses.length)
      : 0

  const misinformationCount = analyses.filter((analysis) => analysis.misinformation_flag).length

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl md:text-4xl font-bold mb-4">Analysis Dashboard</h1>
        <p className="text-lg text-muted-foreground">View your analysis history and insights</p>
      </div>

      {/* Stats Overview */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Analyses</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyses.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Trust Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getTrustScoreColor(averageTrustScore)}`}>{averageTrustScore}%</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Misinformation Flags</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{misinformationCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* Analysis History */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis History</CardTitle>
          <CardDescription>Your recent text analyses and their results</CardDescription>
        </CardHeader>
        <CardContent>
          {analyses.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No analyses yet</h3>
              <p className="text-muted-foreground mb-4">Start analyzing text to see your results here</p>
              <Button onClick={() => router.push("/analyze")}>Analyze Your First Text</Button>
            </div>
          ) : (
            <div className="space-y-4">
              {analyses.map((analysis) => (
                <Card key={analysis.id} className="border-l-4 border-l-primary">
                  <CardContent className="pt-6">
                    <div className="space-y-4">
                      {/* Header */}
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {analysis.original_text.substring(0, 150)}...
                          </p>
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">{formatDate(analysis.created_at)}</span>
                        </div>
                      </div>

                      {/* Metrics */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <div className="text-sm text-muted-foreground">Trust Score</div>
                          <div className={`text-lg font-bold ${getTrustScoreColor(analysis.trust_score)}`}>
                            {analysis.trust_score}%
                          </div>
                          <Progress value={analysis.trust_score} className="h-2 mt-1" />
                        </div>

                        <div>
                          <div className="text-sm text-muted-foreground">Sentiment</div>
                          <div className="flex items-center gap-2 mt-1">
                            {getSentimentIcon(analysis.sentiment)}
                            <Badge variant="outline" className="capitalize text-xs">
                              {analysis.sentiment}
                            </Badge>
                          </div>
                        </div>

                        <div>
                          <div className="text-sm text-muted-foreground">Bias Type</div>
                          <Badge variant="secondary" className="mt-1 text-xs">
                            {analysis.bias_type === "none" ? "No Bias" : analysis.bias_type}
                          </Badge>
                        </div>

                        <div>
                          <div className="text-sm text-muted-foreground">Misinformation</div>
                          <div className="mt-1">
                            {analysis.misinformation_flag ? (
                              <Badge variant="destructive" className="text-xs">
                                <AlertTriangle className="h-3 w-3 mr-1" />
                                Flagged
                              </Badge>
                            ) : (
                              <Badge variant="default" className="text-xs">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Clear
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Emotional Language */}
                      {analysis.emotional_language && analysis.emotional_language.length > 0 && (
                        <div>
                          <div className="text-sm text-muted-foreground mb-2">Emotional Language:</div>
                          <div className="flex flex-wrap gap-1">
                            {analysis.emotional_language.slice(0, 5).map((phrase, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                "{phrase}"
                              </Badge>
                            ))}
                            {analysis.emotional_language.length > 5 && (
                              <Badge variant="outline" className="text-xs">
                                +{analysis.emotional_language.length - 5} more
                              </Badge>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
