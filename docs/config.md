## 本地运行

后端
```
cd backend
uv venv
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload
```

前端
```
cd frontend
pnpm install
pnpm dev
```

## 环境变量
- MODELSCOPE_API_KEY: ModelScope API Key
- MODELSCOPE_API_BASE: ModelScope API Base URL
- MODELSCOPE_MODEL: 模型名
- DATA_DIR: 数据目录
