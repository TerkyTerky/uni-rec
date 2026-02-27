import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { fetchUsers } from "@/api"

type Params = {
  reviewerID: string
  threshold: number
  topK: number
  useLLM: boolean
}

type User = {
  reviewerID: string
  reviewerName: string
}

type Props = {
  params: Params
  onChange: (params: Params) => void
  onGenerate: () => void
  onRecommend: () => void
  loading: boolean
}

export default function ControlPanel({ params, onChange, onGenerate, onRecommend, loading }: Props) {
  const [users, setUsers] = useState<User[]>([])

  useEffect(() => {
    fetchUsers().then(res => {
      setUsers(res.data)
      if (res.data.length > 0 && !params.reviewerID) {
        update("reviewerID", res.data[0].reviewerID)
      }
    })
  }, [])

  const update = (key: keyof Params, value: string | number | boolean) => {
    onChange({ ...params, [key]: value })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>控制面板</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>选择用户 (reviewerID)</Label>
          <Select value={params.reviewerID} onValueChange={(val) => update("reviewerID", val)}>
            <SelectTrigger>
              <SelectValue placeholder="Select user" />
            </SelectTrigger>
            <SelectContent>
              {users.map(u => (
                <SelectItem key={u.reviewerID} value={u.reviewerID}>
                  {u.reviewerName} ({u.reviewerID})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>冷启动阈值</Label>
          <Input
            type="number"
            value={params.threshold}
            onChange={(e) => update("threshold", Number(e.target.value))}
          />
        </div>
        <div className="space-y-2">
          <Label>TopK</Label>
          <Input
            type="number"
            value={params.topK}
            onChange={(e) => update("topK", Number(e.target.value))}
          />
        </div>
        <div className="flex items-center justify-between">
          <Label>使用LLM</Label>
          <Switch checked={params.useLLM} onCheckedChange={(value) => update("useLLM", value)} />
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onGenerate}>
            生成模拟数据
          </Button>
          <Button onClick={onRecommend} disabled={loading}>
            {loading ? "推荐中..." : "获取推荐"}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
