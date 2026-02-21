import os


class Settings:
    def __init__(self) -> None:
        self.modelscope_api_key = os.getenv("MODELSCOPE_API_KEY", "")
        self.modelscope_api_base = os.getenv(
            "MODELSCOPE_API_BASE",
            "https://api-inference.modelscope.cn/v1/chat/completions",
        )
        self.modelscope_model = os.getenv("MODELSCOPE_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        self.data_dir = os.getenv("DATA_DIR", "")


settings = Settings()
