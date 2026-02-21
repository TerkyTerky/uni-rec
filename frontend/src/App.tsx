import { useEffect, useMemo, useState } from "react"
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
    const result = await requestRecommend({
      reviewerID: params.reviewerID,
      top_k: params.topK,
      threshold: params.threshold,
      mode: "auto",
      use_llm: params.useLLM
    })
    setStartupType(result.data.startup_type)
    setRecommendations(result.data.items)
    setSummary(result.data.summary)
    if (result.data.module === "sequence") {
      const seq = await fetchSequence(params.reviewerID)
      setSequenceEvents(seq.data.events)
      setSocialGraph({ nodes: [], edges: [] })
    } else {
      const graph = await fetchSocialGraph(params.reviewerID)
      setSocialGraph(graph.data)
      setSequenceEvents([])
    }
    const metricRes = await fetchMetrics()
    setMetrics(metricRes.data.metrics)
    setLoading(false)
  }

  const handleFeedback = async (asin: string, action: "like" | "dislike" | "save") => {
    await sendFeedback({
      reviewerID: params.reviewerID,
      asin,
      action
    })
    const metricRes = await fetchMetrics()
    setMetrics(metricRes.data.metrics)
  }

  useEffect(() => {
    const init = async () => {
      const type = await fetchStartupType(params.reviewerID, params.threshold)
      setStartupType(type.data.startup_type)
      const metricRes = await fetchMetrics()
      setMetrics(metricRes.data.metrics)
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
        <div>
          <Card>
            <CardHeader>
              <CardTitle>{moduleTitle}可视化</CardTitle>
            </CardHeader>
            <CardContent>
              {startupType === "hot" ? (
                <TimelineChart events={sequenceEvents} />
              ) : (
                <SocialGraph graph={socialGraph} />
              )}
            </CardContent>
          </Card>
        </div>
        <div className="flex flex-col gap-4">
          <RecommendationPanel
            summary={summary}
            items={recommendations}
            onFeedback={handleFeedback}
          />
        </div>
      </div>
    </div>
  )
}
