from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:////tmp/jintianchisha.db")
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_VERIFICATION_TOKEN: str = ""
    FEISHU_ENCRYPT_KEY: str = ""
    BAIDU_MAP_AK: str = ""
    AMAP_KEY: str = ""
    API_PREFIX: str = "/api"
    
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

settings = Settings()