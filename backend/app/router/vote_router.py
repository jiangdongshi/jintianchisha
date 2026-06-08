from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.service.vote_service import add_vote, get_user_votes, get_top_restaurants
from app.schemas import VoteRecord, VoteRecordCreate

router = APIRouter(prefix="/votes", tags=["votes"])

@router.post("/", response_model=VoteRecord)
def create_vote(vote: VoteRecordCreate, db: Session = Depends(get_db)):
    return add_vote(db=db, vote=vote)

@router.get("/user/{user_id}", response_model=list[VoteRecord])
def read_user_votes(user_id: str, db: Session = Depends(get_db)):
    votes = get_user_votes(db, user_id=user_id)
    return votes

@router.get("/top", response_model=list)
def read_top_voted_restaurants(limit: int = 10, db: Session = Depends(get_db)):
    top_restaurants = get_top_restaurants(db, limit=limit)
    return [{"restaurant_id": r[0], "vote_count": r[1]} for r in top_restaurants]