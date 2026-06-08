from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.router import restaurant_router, vote_router, lottery_router, feishu_router, map_router
from app.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="今天吃啥", description="一个帮助你决定吃什么的小应用")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(restaurant_router.router, prefix=settings.API_PREFIX)
app.include_router(vote_router.router, prefix=settings.API_PREFIX)
app.include_router(lottery_router.router, prefix=settings.API_PREFIX)
app.include_router(feishu_router.router, prefix=settings.API_PREFIX)
app.include_router(map_router.router, prefix=settings.API_PREFIX)

@app.get("/")
def root():
    return {"message": "今天吃啥 API 服务已启动！", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
