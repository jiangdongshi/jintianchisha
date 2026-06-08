from sqlalchemy.orm import Session
from app.repo.restaurant_repo import (
    get_restaurant,
    get_restaurants,
    create_restaurant,
    update_restaurant,
    delete_restaurant
)
from app.schemas import RestaurantCreate, RestaurantUpdate

def get_restaurant_by_id(db: Session, restaurant_id: int):
    return get_restaurant(db, restaurant_id)

def get_all_restaurants(db: Session, skip: int = 0, limit: int = 100):
    return get_restaurants(db, skip, limit)

def create_new_restaurant(db: Session, restaurant: RestaurantCreate):
    return create_restaurant(db, restaurant)

def update_existing_restaurant(db: Session, restaurant_id: int, restaurant: RestaurantUpdate):
    return update_restaurant(db, restaurant_id, restaurant)

def remove_restaurant(db: Session, restaurant_id: int):
    return delete_restaurant(db, restaurant_id)