from sqlalchemy.orm import Session
from app.repo.vote_repo import (
    create_vote,
    get_votes_by_user,
    get_top_voted_restaurants
)
from app.schemas import VoteRecordCreate

def add_vote(db: Session, vote: VoteRecordCreate):
    return create_vote(db, vote)

def get_user_votes(db: Session, user_id: str):
    return get_votes_by_user(db, user_id)

def get_top_restaurants(db: Session, limit: int = 10):
    return get_top_voted_restaurants(db, limit)