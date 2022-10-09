from sqlalchemy.orm import Session
from datetime import date
import models, schemas

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email, username=user.username,
                          pw_hash=user.pw_hash, pw_salt=user.pw_salt)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def def_get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def create_user_goal(db: Session, goal: schemas.GoalCreate, user_id: int):
    db_goal = models.Goal(**goal.dict(), creator_id=user_id, start_date=date.today(),
                          next_check_in=date.today(), check_in_num=0)
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal
