# uni-rec

## 项目概述
uni-rec 是一个用于演示推荐系统流程的全栈项目，后端使用 FastAPI 提供推荐与分析接口，前端使用 Vite + React 展示推荐结果、序列可视化与社交图。

## 功能模块
- 数据加载与存储：支持从 MongoDB 或本地 Electronics 数据文件初始化数据 [data_store.py](file:///Users/bytedance/Desktop/personal/uni-rec/backend/app/services/data_store.py#L1-L238)
- 推荐服务：冷热启动判断、序列推荐与社交推荐，支持 LLM 统一生成推荐理由 [recommendation.py](file:///Users/bytedance/Desktop/personal/uni-rec/backend/app/services/recommendation.py#L1-L157)
- 指标与反馈：CTR、覆盖率、多样性统计与反馈记录 [metrics.py](file:///Users/bytedance/Desktop/personal/uni-rec/backend/app/services/metrics.py#L1-L26) [feedback.py](file:///Users/bytedance/Desktop/personal/uni-rec/backend/app/services/feedback.py#L1-L9)
- 前端展示：推荐列表、序列时间线、社交图与指标面板 [App.tsx](file:///Users/bytedance/Desktop/personal/uni-rec/frontend/src/App.tsx#L1-L169)

## 快速开始
**后端**
```bash
cd backend
uv venv
uv pip install -r requirements.txt
MONGO_URI="mongodb://localhost:27017" \
MONGO_DB="uni_rec" \
uvicorn app.main:app --reload --port 8000
```

**前端**
```bash
cd frontend
pnpm install
pnpm dev
```

## 接口概览
接口清单与详细示例见 DOCUMENTATION.md。

## 部署指南
部署细节、配置项与流程图说明见 DOCUMENTATION.md。
