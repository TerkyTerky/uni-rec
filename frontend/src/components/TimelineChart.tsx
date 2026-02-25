import { useEffect, useRef } from "react"
import * as echarts from "echarts"

type Event = {
  unixReviewTime: number
  overall: number
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
      tooltip: {
        trigger: "axis",
        formatter: (params: any) => {
          const data = params[0].data
          return `${params[0].name}<br/>评分: ${data}`
        }
      },
      xAxis: {
        type: "category",
        name: "时间",
        data: events.map((e) => new Date(e.unixReviewTime * 1000).toLocaleDateString())
      },
      yAxis: {
        type: "value",
        name: "评分",
        min: 0,
        max: 5,
        interval: 1
      },
      series: [
        {
          data: events.map((e) => e.overall),
          type: "line",
          smooth: true,
          markPoint: {
            data: [
              { type: "max", name: "最高分" },
              { type: "min", name: "最低分" }
            ]
          }
        }
      ]
    }
    chart.setOption(option)
    return () => chart.dispose()
  }, [events])

  return <div className="h-[360px] w-full" ref={chartRef} />
}
