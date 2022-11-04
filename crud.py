import enum
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


def create_goal(db: Session, goal_name: str, check_in_period: int,
                template_id: int, user_id: int):
    db_goal = models.Goal(goal_name=goal_name, template_id=template_id, creator_id=user_id,
                          start_date=date.today(), check_in_num=0,
                          check_in_period=check_in_period,
                          next_check_in=date.today() + timedelta(days=check_in_period))
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal


def get_user_goals(username: str, db: Session, skip: int = 0, limit: int = 100):
    user = db.query(models.User).filter(models.User.username == username).first()
    return user.goals


def delete_user(db: Session, user_id: int):
    deleted = db.query(models.User).filter(models.User.id == user_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return "Successful deletion"
    else:
        return "User not found"


def delete_goal(db: Session, goal_id: int):
    deleted = db.query(models.Goal).filter(models.Goal.id == goal_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return True
    else:
        return False


def create_template(db: Session, name: str, is_custom: bool, creator_id: int):
    db_template = models.Template(name=name)
    if not is_custom:
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


def create_question(db: Session, text: str, template_id: int, response_type: enum,
                    next_check_in_period: int):
    db_question = models.Question(text=text, template_id=template_id,
                                  response_type=response_type, check_in_num=0,
                                  next_check_in_period=next_check_in_period)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def create_response(db: Session, text: str, question_id: int, check_in_number: int, goal_id: int):
    db_response = models.Response(question_id=question_id, goal_id=goal_id, text=text,
                                  check_in_number=check_in_number)
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response


def get_premade_templates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Template).filter(models.Template.is_custom == False).offset(skip).limit(limit).all()


def get_questions_by_template(db: Session, template_id: int):
    return db.query(models.Question).filter(models.Question.template_id == template_id).all()


def get_question(db: Session, question_id: int):
    return db.query(models.Question).filter(models.Question.question_id == question_id).first()


def get_responses_by_goal(db: Session, goal_id: int):
    return db.query(models.Response).filter(models.Response.goal_id == goal_id).all()


def get_responses_by_question(db: Session, question_id: int):
    return db.query(models.Response).filter(models.Response.question_id == question_id).all()


def update_goal_check_in_period(db: Session, goal_id: int, new_check_in: int):
    goal = get_goal(db, goal_id)
    if goal:
        goal.check_in_period = new_check_in
        goal.next_check_in = goal.start_date + timedelta(days=goal.check_in_period)
        db.commit()
        db.refresh(goal)
        return True
    return False


def mark_goal_achieved(db: Session, goal_id: int):
    goal = get_goal(db, goal_id)
    if goal:
        goal.is_achieved = True
        db.commit()
        db.refresh(goal)
        return True
    return False


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
