"""
备选餐厅初始化脚本：默认是空的，餐厅全部来自百度地图实时搜索。
- 如果你想跑起来就有些数据（纯本地测试用），在 seed_data 列表里填餐厅即可。
- 真正的「按位置抽」会调用 /api/lottery/draw/nearby，完全忽略这里的预设。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.database import SessionLocal, engine, Base
from app.schemas import RestaurantCreate
from app.repo.restaurant_repo import create_restaurant
from app.models import Restaurant, VoteRecord, LotteryRecord

Base.metadata.create_all(bind=engine)

seed_data = []


def main():
    db = SessionLocal()
    try:
        for item in seed_data:
            restaurant = RestaurantCreate(**item)
            db_restaurant = create_restaurant(db, restaurant)
            print(f"✅ 已添加: {db_restaurant.name}")
        if not seed_data:
            print("ℹ️  没有预设餐厅，稍后通过百度地图 API 实时导入。")
        else:
            print(f"\n🎉 共添加 {len(seed_data)} 家餐厅")
    finally:
        db.close()


if __name__ == "__main__":
    main()
