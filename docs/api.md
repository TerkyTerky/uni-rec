## 基础信息
Base URL: `http://localhost:8000/api`

## 接口列表

### POST /data/generate
生成模拟数据

请求体
```
{
  "users": 30,
  "items": 80,
  "behaviors_per_user": 20,
  "social_degree": 3,
  "seed": 42
}
```

响应
```
{
  "users": 30,
  "items": 80,
  "behaviors": 600,
  "social_edges": 90
}
```

### GET /users/{user_id}
获取用户画像

### GET /users/{user_id}/startup-type
获取冷/热启动判定

Query 参数
- threshold: 冷启动阈值

### GET /users/{user_id}/sequence
获取用户行为序列

### GET /users/{user_id}/social-graph
获取社交图谱

### POST /recommend
获取推荐结果

请求体
```
{
  "user_id": "user_0",
  "top_k": 10,
  "threshold": 5,
  "mode": "auto",
  "use_llm": true
}
```

响应
```
{
  "user_id": "user_0",
  "startup_type": "hot",
  "module": "sequence",
  "items": [],
  "summary": ""
}
```

### POST /feedback
提交用户反馈

请求体
```
{
  "user_id": "user_0",
  "item_id": "item_1",
  "action": "like"
}
```

### GET /metrics
获取监控指标
