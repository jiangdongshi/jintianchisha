from sqlalchemy.orm import Session
from app.models import Restaurant
from app.schemas import RestaurantCreate, RestaurantUpdate

def get_restaurant(db: Session, restaurant_id: int):
    return db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

def get_restaurants(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Restaurant).filter(Restaurant.is_active == True).offset(skip).limit(limit).all()

def create_restaurant(db: Session, restaurant: RestaurantCreate):
    db_restaurant = Restaurant(**restaurant.dict())
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant

def update_restaurant(db: Session, restaurant_id: int, restaurant: RestaurantUpdate):
    db_restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if db_restaurant:
        update_data = restaurant.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_restaurant, key, value)
        db.commit()
        db.refresh(db_restaurant)
    return db_restaurant

def delete_restaurant(db: Session, restaurant_id: int):
    db_restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if db_restaurant:
        db_restaurant.is_active = False
        db.commit()
        db.refresh(db_restaurant)
    return db_restaurant


def delete_all_restaurants(db: Session) -> int:
    """
    物理删除所有餐厅，用于「切换搜索条件时清空备选」场景。
    返回被删除的条数。
    """
    deleted = db.query(Restaurant).delete(synchronize_session=False)
    db.commit()
    return int(deleted)
