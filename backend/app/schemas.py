from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class RestaurantBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[int] = None
    price: Optional[int] = None
    tags: Optional[str] = None
    image_url: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantUpdate(RestaurantBase):
    is_active: Optional[bool] = None

class Restaurant(RestaurantBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class VoteRecordBase(BaseModel):
    restaurant_id: int
    user_id: str
    user_name: Optional[str] = None

class VoteRecordCreate(VoteRecordBase):
    pass

class VoteRecord(VoteRecordBase):
    id: int
    vote_time: datetime
    
    model_config = {"from_attributes": True}

class LotteryRecordBase(BaseModel):
    restaurant_id: int
    winner_user_id: Optional[str] = None
    winner_user_name: Optional[str] = None

class LotteryRecordCreate(LotteryRecordBase):
    pass

class LotteryRecord(LotteryRecordBase):
    id: int
    lottery_time: datetime
    
    model_config = {"from_attributes": True}

class LotteryResult(BaseModel):
    restaurant: Restaurant
    lottery_time: datetime