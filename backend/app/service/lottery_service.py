import random
from sqlalchemy.orm import Session
from app.repo.restaurant_repo import get_restaurants
from app.repo.lottery_repo import create_lottery_record, get_recent_lottery_records
from app.schemas import LotteryRecordCreate, LotteryResult

def perform_lottery(db: Session, winner_user_id: str = None, winner_user_name: str = None):
    restaurants = get_restaurants(db)
    if not restaurants:
        return None
    
    selected = random.choice(restaurants)
    
    lottery_data = LotteryRecordCreate(
        restaurant_id=selected.id,
        winner_user_id=winner_user_id,
        winner_user_name=winner_user_name
    )
    created_record = create_lottery_record(db, lottery_data)
    
    return LotteryResult(
        restaurant=selected,
        lottery_time=created_record.lottery_time
    )

def get_recent_lotteries(db: Session, limit: int = 10):
    return get_recent_lottery_records(db, limit)