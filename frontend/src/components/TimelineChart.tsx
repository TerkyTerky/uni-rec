import { useEffect, useRef } from "react"
import * as echarts from "echarts"

type Event = {
  unixReviewTime: number
}

type Props = {
  events: Event[]
}

export default function TimelineChart({ events }: Props) {
  const chartRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!chartRef.current) return
    const chart = echarts.init(chartRef.current)
    const option = {
      tooltip: { trigger: "axis" },
      xAxis: {
        type: "category",
        data: events.map((e) => new Date(e.unixReviewTime * 1000).toLocaleTimeString())
      },
      yAxis: { type: "value" },
      series: [
        {
          data: events.map((_, index) => index + 1),
          type: "line",
          smooth: true
        }
      ]
    }
    chart.setOption(option)
    return () => chart.dispose()
  }, [events])

  return <div className="h-[360px] w-full" ref={chartRef} />
}
