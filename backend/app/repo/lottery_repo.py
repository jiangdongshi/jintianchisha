from sqlalchemy.orm import Session
from app.models import LotteryRecord
from app.schemas import LotteryRecordCreate

def create_lottery_record(db: Session, lottery: LotteryRecordCreate):
    db_lottery = LotteryRecord(**lottery.dict())
    db.add(db_lottery)
    db.commit()
    db.refresh(db_lottery)
    return db_lottery

def get_lottery_records(db: Session, skip: int = 0, limit: int = 100):
    return db.query(LotteryRecord).offset(skip).limit(limit).all()

def get_recent_lottery_records(db: Session, limit: int = 10):
    return db.query(LotteryRecord).order_by(LotteryRecord.lottery_time.desc()).limit(limit).all()