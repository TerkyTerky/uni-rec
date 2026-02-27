import { useEffect, useRef } from "react"
import * as echarts from "echarts"

type Event = {
  unixReviewTime: number
  overall: number
  summary?: string
  title?: string
  category?: string
  type?: string
}

type Props = {
  events: Event[]
}

export default function TimelineChart({ events }: Props) {
  const chartRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!chartRef.current) return
    const chart = echarts.init(chartRef.current)
    
    // Sort events by time ascending for the chart
    const sortedEvents = [...events].sort((a, b) => a.unixReviewTime - b.unixReviewTime)
    
    const option = {
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "line" },
        formatter: (params: any) => {
          if (!params || !params.length) return ""
          const data = params[0].data
          // Use original data from params.data, not value array
          const dateStr = new Date(data.unixReviewTime * 1000).toLocaleString()
          return `
            <div style="font-size:12px">
              <b>${data.title || 'Unknown'}</b><br/>
              ${data.type === 'feedback' ? `Feedback: ${data.summary}` : `Review: ${data.overall} stars`}<br/>
              Category: ${data.category || 'N/A'}<br/>
              Time: ${dateStr}
            </div>
          `
        }
      },
      xAxis: {
        type: "category",
        name: "Interaction Order",
        data: sortedEvents.map((_, index) => index + 1), // 1, 2, 3...
        splitLine: { show: false }
      },
      yAxis: {
        type: "value",
        name: "Rating",
        min: 0,
        max: 6,
        interval: 1,
        splitLine: { show: true, lineStyle: { type: 'dashed' } }
      },
      series: [
        {
          name: "Interactions",
          type: "line", // Use line chart directly to connect points
          smooth: true,
          symbolSize: 12,
          showSymbol: true, // Force show symbols for all points including the last one
          symbol: "circle", // Solid circle
          lineStyle: { width: 2, color: '#94a3b8' },
          data: sortedEvents.map((e, index) => {
            // Determine color based on rating for all events (both historical and feedback)
            // Gradient from Red (1) to Green (5)
            // 1: #ef4444 (Red)
            // 2: #f97316 (Orange)
            // 3: #eab308 (Yellow)
            // 4: #84cc16 (Lime)
            // 5: #22c55e (Green)
            const colors = {
              1: '#ef4444',
              2: '#f97316',
              3: '#eab308',
              4: '#84cc16',
              5: '#22c55e'
            }
            // @ts-ignore
            let color = colors[Math.round(e.overall)] || '#22c55e'
            
            // Fallback for 0 or unexpected values (e.g. initial placeholder) -> Gray
            if (e.overall < 1) color = '#94a3b8'

            return {
              value: [index, e.overall], // x=index, y=rating
              ...e,
              itemStyle: {
                color: color,
                borderColor: '#ffffff',
                borderWidth: 2
              },
              // ECharts sometimes needs explicit emphasis style to maintain color
              emphasis: {
                itemStyle: {
                  color: color
                }
              }
            }
          })
        }
      ]
    }
    chart.setOption(option)
    
    const handleResize = () => chart.resize()
    window.addEventListener("resize", handleResize)
    return () => {
      chart.dispose()
      window.removeEventListener("resize", handleResize)
    }
  }, [events])

  return <div className="h-[360px] w-full" ref={chartRef} />
}
