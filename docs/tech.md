## 架构概览
本项目采用前后端分离架构，前端基于 React + TypeScript + ECharts + shadcn/ui + Tailwind，后端使用 FastAPI 提供 API 服务，推荐模块内置在后端服务中，通过冷启动/热启动分支路由选择社交推荐或序列推荐。

## 运行环境
- Mac 本地运行
- 后端依赖管理：uv
- 前端依赖管理：pnpm

## 模块划分
- 数据生成与预处理：后端 `app/services/data_generator.py` 与 `app/services/preprocess.py`
- 冷/热启动判定：后端 `app/services/recommendation.py`
- 序列推荐：后端 `app/services/recommendation.py`
- 社交推荐：后端 `app/services/recommendation.py`
- LLM 适配：后端 `app/core/llm.py`
- 前端可视化：`frontend/src/components`

## 推荐策略
- 冷启动用户：基于社交邻居行为与影响力推荐
- 热启动用户：基于行为序列与类别偏好推荐
- 推荐理由：优先使用 ModelScope API 生成，失败时回退为规则解释

## 可视化方案
- 热启动：时间序列折线图展示行为序列
- 冷启动：社交图谱展示用户关系与连接强度
- 指标：CTR、覆盖率、多样性、反馈计数
