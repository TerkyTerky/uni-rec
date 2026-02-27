import { useEffect, useMemo, useState } from "react"
import { fetchEventSource } from "@microsoft/fetch-event-source"
import {
  fetchMetrics,
  fetchSequence,
  fetchSocialGraph,
  fetchStartupType,
  generateData,
  requestRecommend,
  sendFeedback
} from "@/api"
import ControlPanel from "@/components/ControlPanel"
import RecommendationPanel from "@/components/RecommendationPanel"
import TimelineChart from "@/components/TimelineChart"
import SocialGraph from "@/components/SocialGraph"
import MetricsDashboard from "@/components/MetricsDashboard"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type Params = {
  reviewerID: string
  threshold: number
  topK: number
  useLLM: boolean
}

type RecommendationItem = {
  asin: string
  score: number
  reason: string
  source: string
  meta: {
    title: string
    categories?: string[][]
  }
}

type SequenceEvent = {
  asin: string
  overall: number
  unixReviewTime: number
  title?: string
  category?: string
}

type SocialGraphData = {
  nodes: Array<{ id: string; name: string; category: number; symbolSize: number; value?: number }>
  edges: Array<{ source: string; target: string; value: number }>
}

const defaultParams: Params = {
  reviewerID: "A1234567",
  threshold: 5,
  topK: 10,
  useLLM: true
}

export default function App() {
  const [params, setParams] = useState<Params>(defaultParams)
  const [startupType, setStartupType] = useState<"hot" | "cold">("hot")
  const [sequenceEvents, setSequenceEvents] = useState<SequenceEvent[]>([])
  const [socialGraph, setSocialGraph] = useState<SocialGraphData>({ nodes: [], edges: [] })
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([])
  const [summary, setSummary] = useState("")
  const [thinking, setThinking] = useState("")
  const [metrics, setMetrics] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(false)

  const handleGenerate = async () => {
    await generateData({
      users: 30,
      items: 80,
      behaviors_per_user: 20,
      social_degree: 3,
      seed: 42
    })
  }

  const handleRecommend = async () => {
    setLoading(true)
    setThinking("")
    setRecommendations([])
    setSummary("计算中...")
    
    try {
      await fetchEventSource("http://localhost:8000/api/recommend", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          reviewerID: params.reviewerID,
          top_k: params.topK,
          threshold: params.threshold,
          mode: "auto",
          use_llm: params.useLLM
        }),
        onmessage(ev) {
          if (ev.event === "done") {
             // Close connection
             return
          }
          
          const data = JSON.parse(ev.data)
          
          if (!ev.event) {
            // Initial payload
            setStartupType(data.startup_type)
            setRecommendations(data.items)
            setSummary(data.summary)
            
            // Trigger visual updates
            if (data.module === "sequence") {
               fetchSequence(params.reviewerID).then(res => setSequenceEvents(res.data.events))
               fetchSocialGraph(params.reviewerID).then(res => setSocialGraph(res.data))
            } else {
               fetchSocialGraph(params.reviewerID).then(res => setSocialGraph(res.data))
               fetchSequence(params.reviewerID).then(res => setSequenceEvents(res.data.events))
            }
          } else if (ev.event === "thinking") {
            setThinking(prev => prev + data.content)
          } else if (ev.event === "reasoning") {
            // Can display incremental reasoning if needed
          } else if (ev.event === "update") {
            setRecommendations(data.items)
          }
        },
        onerror(err) {
           console.error("SSE error:", err)
           setLoading(false)
           throw err
        },
        onclose() {
           setLoading(false)
        }
      })
    } catch (e) {
      console.error(e)
    } finally {
       setLoading(false)
       const metricRes = await fetchMetrics()
       setMetrics(metricRes.data.metrics)
    }
  }

  const handleFeedback = async (asin: string, score: number) => {
    await sendFeedback({
      reviewerID: params.reviewerID,
      asin,
      score
    })
    const metricRes = await fetchMetrics()
    setMetrics(metricRes.data.metrics)
    
    // Refresh timeline
    const seq = await fetchSequence(params.reviewerID)
    setSequenceEvents(seq.data.events)
  }

  useEffect(() => {
    const init = async () => {
      const type = await fetchStartupType(params.reviewerID, params.threshold)
      setStartupType(type.data.startup_type)
      const metricRes = await fetchMetrics()
      setMetrics(metricRes.data.metrics)
      
      // Load sequence and social graph immediately
      const seq = await fetchSequence(params.reviewerID)
      setSequenceEvents(seq.data.events)
      
      const graph = await fetchSocialGraph(params.reviewerID)
      setSocialGraph(graph.data)
    }
    init()
  }, [params.reviewerID, params.threshold])

  const moduleTitle = useMemo(() => {
    return startupType === "hot" ? "序列推荐" : "社交推荐"
  }, [startupType])

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-6 text-slate-900">
      <header className="mb-5">
        <h1 className="text-2xl font-semibold">uni-rec 推荐系统模拟器</h1>
        <p className="text-sm text-slate-500">
          当前用户类型：{startupType === "hot" ? "热启动" : "冷启动"}
        </p>
      </header>
      <div className="grid grid-cols-[280px_1fr_380px] gap-4">
        <div className="flex flex-col gap-4">
          <ControlPanel
            params={params}
            onChange={setParams}
            onGenerate={handleGenerate}
            onRecommend={handleRecommend}
            loading={loading}
          />
          <MetricsDashboard metrics={metrics} />
        </div>
        <div className="flex flex-col gap-4">
          <Card className={startupType === "hot" ? "border-primary shadow-md ring-1 ring-primary" : "opacity-60 grayscale"}>
            <CardHeader>
              <CardTitle>序列推荐可视化 (热启动)</CardTitle>
            </CardHeader>
            <CardContent>
              <TimelineChart events={sequenceEvents} />
            </CardContent>
          </Card>
          
          <Card className={startupType === "cold" ? "border-primary shadow-md ring-1 ring-primary" : "opacity-60 grayscale"}>
            <CardHeader>
              <CardTitle>社交推荐可视化 (冷启动)</CardTitle>
            </CardHeader>
            <CardContent>
              <SocialGraph graph={socialGraph} />
            </CardContent>
          </Card>
        </div>
        <div className="flex flex-col gap-4">
          <RecommendationPanel
            summary={summary}
            items={recommendations}
            thinking={thinking}
            onFeedback={handleFeedback}
          />
        </div>
      </div>
    </div>
  )
}
