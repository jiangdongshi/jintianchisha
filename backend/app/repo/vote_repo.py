from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import VoteRecord
from app.schemas import VoteRecordCreate

def create_vote(db: Session, vote: VoteRecordCreate):
    db_vote = VoteRecord(**vote.dict())
    db.add(db_vote)
    db.commit()
    db.refresh(db_vote)
    return db_vote

def get_votes_by_restaurant(db: Session, restaurant_id: int):
    return db.query(VoteRecord).filter(VoteRecord.restaurant_id == restaurant_id).all()

def get_votes_by_user(db: Session, user_id: str):
    return db.query(VoteRecord).filter(VoteRecord.user_id == user_id).all()

def get_vote_count_by_restaurant(db: Session, restaurant_id: int):
    return db.query(func.count(VoteRecord.id)).filter(VoteRecord.restaurant_id == restaurant_id).scalar()

def get_top_voted_restaurants(db: Session, limit: int = 10):
    return db.query(
        VoteRecord.restaurant_id,
        func.count(VoteRecord.id).label('vote_count')
    ).group_by(VoteRecord.restaurant_id).order_by(func.count(VoteRecord.id).desc()).limit(limit).all()