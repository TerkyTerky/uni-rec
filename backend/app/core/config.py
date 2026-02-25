import os


class Settings:
    def __init__(self) -> None:
        self.ark_api_key = os.getenv("ARK_API_KEY", "e568f04e-3f64-4fe0-baf7-3fd6d154742c")
        self.ark_api_base = os.getenv(
            "ARK_API_BASE",
            "https://ark.cn-beijing.volces.com/api/v3",
        )
        self.ark_model = os.getenv("ARK_MODEL_ID", "doubao-seed-2-0-pro-260215")
        self.data_dir = os.getenv("DATA_DIR", "")


settings = Settings()
