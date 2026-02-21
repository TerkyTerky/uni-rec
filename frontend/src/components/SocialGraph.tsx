import { useEffect, useRef } from "react"
import * as echarts from "echarts"

type Node = {
  id: string
  name: string
  category: number
  symbolSize: number
  value?: number
}

type Edge = {
  source: string
  target: string
  value: number
}

type Props = {
  graph: {
    nodes: Node[]
    edges: Edge[]
  }
}

export default function SocialGraph({ graph }: Props) {
  const chartRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!chartRef.current) return
    const chart = echarts.init(chartRef.current)
    const option = {
      tooltip: {},
      series: [
        {
          type: "graph",
          layout: "force",
          roam: true,
          data: graph.nodes,
          links: graph.edges,
          label: { show: true },
          force: { repulsion: 120 }
        }
      ]
    }
    chart.setOption(option)
    return () => chart.dispose()
  }, [graph])

  return <div className="h-[360px] w-full" ref={chartRef} />
}
