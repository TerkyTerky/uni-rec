from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env file
load_dotenv()

from app.routes.api import router as api_router
from app.services.data_store import init_store


def create_app() -> FastAPI:
    app = FastAPI(title="uni-rec")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def load_data() -> None:
        await init_store()

    app.include_router(api_router, prefix="/api")
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
