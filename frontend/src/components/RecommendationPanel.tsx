import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import StarRating from "./StarRating"

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
  thinking?: string
  onFeedback: (asin: string, score: number) => void
}

export default function RecommendationPanel({ summary, items, thinking, onFeedback }: Props) {
  const getLeafCategory = (categories?: string[][]) => {
    if (!categories || categories.length === 0 || !categories[0] || categories[0].length === 0) return "Unknown"
    return categories[0][categories[0].length - 1]
  }

  if (!items) return null
  return (
    <Card>
      <CardHeader>
        <CardTitle>推荐结果</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-slate-500">{summary}</p>
        
        {thinking && (
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="thinking">
              <AccordionTrigger className="text-sm text-slate-500">大模型思考过程</AccordionTrigger>
              <AccordionContent>
                <div className="bg-slate-100 p-3 rounded-md text-xs font-mono whitespace-pre-wrap max-h-[200px] overflow-y-auto">
                  {thinking}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        )}

        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.asin} className="flex flex-col gap-3 rounded-lg border border-slate-200 p-3">
              <div>
                <div className="text-sm font-semibold">{item.meta.title}</div>
                <p className="text-sm text-slate-500">{item.reason}</p>
                <Badge className="mt-2">{getLeafCategory(item.meta.categories)}</Badge>
              </div>
              <div className="flex items-center justify-between mt-2 border-t pt-2">
                <span className="text-xs text-slate-500">你的评分：</span>
                <StarRating onChange={(score) => onFeedback(item.asin, score)} />
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
