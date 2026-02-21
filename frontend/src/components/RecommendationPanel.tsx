import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type Item = {
  asin: string
  reason: string
  meta: {
    title: string
    categories?: string[][]
  }
}

type Props = {
  summary: string
  items: Item[]
  onFeedback: (asin: string, action: "like" | "dislike" | "save") => void
}

export default function RecommendationPanel({ summary, items, onFeedback }: Props) {
  const getLeafCategory = (categories?: string[][]) => {
    if (!categories || categories.length === 0 || categories[0].length === 0) return "Unknown"
    return categories[0][categories[0].length - 1]
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>推荐结果</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-slate-500">{summary}</p>
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.asin} className="flex flex-col gap-3 rounded-lg border border-slate-200 p-3">
              <div>
                <div className="text-sm font-semibold">{item.meta.title}</div>
                <p className="text-sm text-slate-500">{item.reason}</p>
                <Badge className="mt-2">{getLeafCategory(item.meta.categories)}</Badge>
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={() => onFeedback(item.asin, "like")}>
                  喜欢
                </Button>
                <Button size="sm" variant="secondary" onClick={() => onFeedback(item.asin, "dislike")}>
                  不喜欢
                </Button>
                <Button size="sm" variant="secondary" onClick={() => onFeedback(item.asin, "save")}>
                  收藏
                </Button>
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
