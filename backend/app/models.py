from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from .database import Base

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    description = Column(Text)
    address = Column(String(200))
    phone = Column(String(20))
    rating = Column(Integer)
    price = Column(Integer)  # 人均消费（元），0 或 None 表示未知
    tags = Column(String(200))
    image_url = Column(String(500))
    latitude = Column(String(50))
    longitude = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class VoteRecord(Base):
    __tablename__ = "vote_records"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, nullable=False)
    user_id = Column(String(100), nullable=False)
    user_name = Column(String(100))
    vote_time = Column(DateTime(timezone=True), server_default=func.now())

class LotteryRecord(Base):
    __tablename__ = "lottery_records"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, nullable=False)
    winner_user_id = Column(String(100))
    winner_user_name = Column(String(100))
    lottery_time = Column(DateTime(timezone=True), server_default=func.now())