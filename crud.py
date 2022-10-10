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

def delete_user(db: Session, user_id: int):
    deleted=db.query(models.User).filter(models.User.id == user_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return "Successful deletion"
    else:
        return "User not found"

def delete_goal(db: Session, goal_id: int):
    deleted=db.query(models.Goal).filter(models.Goal.id == user_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return "Successful deletion"
    else:
        return "Goal not found"

def create_template(db: Session, template: schemas.TemplateCreate):
    db_template = models.Template(name=template.name)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def create_question(db: Session, question: schemas.QuestionCreate, template_id: int):
    db_question = models.Question(text=question.text, template_id=template_id
                                  response_type=question.response_type,check_in_num=0,
                                  next_check_in_period=question.next_check_in_period)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def create_response(db: Session, question: schemas.ResponseCreate):
    db_response = models.Response(**question.dict())
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response
    
                    
                                  
