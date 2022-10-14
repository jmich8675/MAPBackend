from sqlalchemy.orm import Session
from datetime import date, timedelta
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

def get_goal(db: Session, goal_id: int):
    return db.query(models.Goal).filter(models.Goal.id == goal_id).first()

def create_specific_goal(db: Session, goal_name: str, check_in_period: int,
                         template_id: int, user_id: int):
    db_goal = models.Goal(goal_name=goal_name, template_id=template_id, creator_id=user_id, 
                          start_date=date.today(), check_in_num=0, 
                          check_in_period=check_in_period, next_check_in=date.today())
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

def get_user_goals(username: str, db: Session, skip: int = 0, limit: int = 100):
    user=db.query(models.User).filter(models.User.username == username).first()
    return user.goals

def delete_user(db: Session, user_id: int):
    deleted=db.query(models.User).filter(models.User.id == user_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return "Successful deletion"
    else:
        return "User not found"

def delete_goal(db: Session, goal_id: int):
    deleted=db.query(models.Goal).filter(models.Goal.id == goal_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return "Successful deletion"
    else:
        return "Goal not found"

def create_template(db: Session, template: schemas.TemplateCreate, creator_id: int):
    db_template = models.Template(name=template.name)
    if not template.is_custom:
        db_template.is_custom = False
        db_template.creator_id = -1
    else:
        db_template.is_custom = True
        db_template.creator_id = creator_id
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def get_template(db: Session, template_id: int):
    return db.query(models.Template).filter(models.Template.template_id == template_id).first()   

def create_question(db: Session, question: schemas.QuestionCreate, template_id: int):
    db_question = models.Question(text=question.text, template_id=template_id,
                                  response_type=question.response_type,check_in_num=0,
                                  next_check_in_period=question.next_check_in_period)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def create_response(db: Session, response: schemas.ResponseCreate):
    db_response = models.Response(**response.dict())
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response

def get_premade_templates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Template).filter(models.Template.is_custom == False).offset(skip).limit(limit).all()

def get_questions_by_template(db: Session, template_id: int):
    return db.query(models.Question).filter(models.Question.template_id == template_id).all()

def get_responses_by_goal(db: Session, goal_id: int):
    return db.query(models.Response).filter(models.Response.goal_id == goal_id).all()

def get_responses_by_question(db: Session, question_id: int):
    return db.query(models.Response).filter(models.Response.question_id == question_id).all()

def update_goal_checkin_period(db: Session, goal_id: int, new_check_in: timedelta):
    goal = get_goal(db, goal_id)
    if goal:
        goal.check_in_period = new_check_in
        db.commit()
        return "Check in period updated"
    else:
        return "Goal not found"

def mark_goal_achieved(db: Session, goal_id: int):
    goal = get_goal(db, goal_id)
    if goal:
        goal.achieved = True
        db.commit()
        return "Goal Achieved"
    else:
        return "Goal not found"

def toggle_goal_paused(db: Session, goal_id: int):
    goal = get_goal(db, goal_id)
    if goal:
        if goal.is_pause == True:
            goal.is_paused = False
            db.commit()
            return "Goal Unpaused"
        else:
            goal.is_paused = True
            db.commit()
            return "Goal Paused"
    else:
        return "Goal not found"
                  