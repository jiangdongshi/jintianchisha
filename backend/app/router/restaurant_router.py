from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.service.restaurant_service import (
    get_restaurant_by_id,
    get_all_restaurants,
    create_new_restaurant,
    update_existing_restaurant,
    remove_restaurant
)
from app.schemas import Restaurant, RestaurantCreate, RestaurantUpdate

router = APIRouter(prefix="/restaurants", tags=["restaurants"])

@router.get("/", response_model=list[Restaurant])
def read_restaurants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    restaurants = get_all_restaurants(db, skip=skip, limit=limit)
    return restaurants

@router.get("/{restaurant_id}", response_model=Restaurant)
def read_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    db_restaurant = get_restaurant_by_id(db, restaurant_id=restaurant_id)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return db_restaurant

@router.post("/", response_model=Restaurant)
def create_restaurant(restaurant: RestaurantCreate, db: Session = Depends(get_db)):
    return create_new_restaurant(db=db, restaurant=restaurant)

@router.put("/{restaurant_id}", response_model=Restaurant)
def update_restaurant(restaurant_id: int, restaurant: RestaurantUpdate, db: Session = Depends(get_db)):
    db_restaurant = update_existing_restaurant(db=db, restaurant_id=restaurant_id, restaurant=restaurant)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return db_restaurant

@router.delete("/{restaurant_id}", response_model=Restaurant)
def delete_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    db_restaurant = remove_restaurant(db=db, restaurant_id=restaurant_id)
    if db_restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return db_restaurant