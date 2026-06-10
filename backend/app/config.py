from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:////tmp/jintianchisha.db"
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_VERIFICATION_TOKEN: str = ""
    FEISHU_ENCRYPT_KEY: str = ""
    BAIDU_MAP_AK: str = ""
    AMAP_KEY: str = ""
    API_PREFIX: str = "/api"

    class Config:
        env_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".env",
        )
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
