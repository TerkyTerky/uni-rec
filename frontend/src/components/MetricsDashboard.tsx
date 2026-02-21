import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type Props = {
  metrics: Record<string, number>
}

export default function MetricsDashboard({ metrics }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>监控指标</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3 text-sm">
        <div className="flex flex-col gap-1 rounded-lg border border-slate-200 p-2">
          <span className="text-slate-500">CTR</span>
          <strong className="text-base">{metrics.ctr ?? 0}</strong>
        </div>
        <div className="flex flex-col gap-1 rounded-lg border border-slate-200 p-2">
          <span className="text-slate-500">覆盖率</span>
          <strong className="text-base">{metrics.coverage ?? 0}</strong>
        </div>
        <div className="flex flex-col gap-1 rounded-lg border border-slate-200 p-2">
          <span className="text-slate-500">多样性</span>
          <strong className="text-base">{metrics.diversity ?? 0}</strong>
        </div>
        <div className="flex flex-col gap-1 rounded-lg border border-slate-200 p-2">
          <span className="text-slate-500">反馈数</span>
          <strong className="text-base">{metrics.feedback_count ?? 0}</strong>
        </div>
      </CardContent>
    </Card>
  )
}
