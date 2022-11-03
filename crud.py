import enum
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import date, timedelta
import models, schemas



###############################################################################

                        ### (C)RUD CREATE METHODS ###

###############################################################################

def create_question(db: Session, text: str, template_id: int, response_type: enum,
                    next_check_in_period: int):
    db_question = models.Question(text=text, template_id=template_id,
                                  response_type=response_type,check_in_num=0,
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

def create_post(db: Session, title: str, content: str, post_author: int):
    db_post = models.Post(title=title, content=content, post_author=post_author, timestamp=date.now())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def create_comment(db: Session, content:str, post_id: int, comment_author: int):
    db_comment = models.Comment(content=content, timestamp=date.now(), post_id=post_id, comment_author=comment_author)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email, username=user.username,
                          pw_hash=user.pw_hash, pw_salt=user.pw_salt)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

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



###############################################################################

                    ### C(R)UD RETRIEVE/GET METHODS ###

###############################################################################

### GET USERS

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

### GET GOALS

def get_goal(db: Session, goal_id: int):
    return db.query(models.Goal).filter(models.Goal.id == goal_id).first()

def get_user_goals(username: str, db: Session, skip: int = 0, limit: int = 100):
    user=db.query(models.User).filter(models.User.username == username).first()
    return user.goals

def get_checkin_goals(db: Session):
    return db.query(models.Goal).filter(models.Goal.can_check_in == True).all()

def get_achieved_goals(username: str, db: Session):
    user=db.query(models.User).filter(models.User.username == username).first()
    return db.query(models.Goal).filter(models.Goal.creator_id == user.id) \
        .filter(models.Goal.is_achieved == True).all()

def get_unachieved_goals(username: str, db: Session):
    user=db.query(models.User).filter(models.User.username == username).first()
    return db.query(models.Goal).filter(models.Goal.creator_id == user.id) \
        .filter(models.Goal.is_achieved == False).all()

### GET TEMPLATES

def get_template(db: Session, template_id: int):
    return db.query(models.Template).filter(models.Template.template_id == template_id).first()
    
def get_premade_templates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Template).filter(models.Template.is_custom == False).offset(skip).limit(limit).all()       

### GET COMMENTS

def get_comments_by_post(db: Session, post_id: int):
    return db.query(models.Comment).filter(models.Comment.post_id == post_id).all()

def get_comments_by_author(db: Session, user_id: int):
    return db.query(models.Comment).filter(models.Comment.comment_author == user_id).all()

def get_comment_by_id(db: Session, comment_id: int):
    return db.query(models.Comment).filter(models.Comment.comment_id == comment_id).first()

### GET POSTS

def get_posts_by_author(db: Session, post_author: int):
    return db.query(models.Post).filter(models.Post.post_author == post_author).all()

def get_post_by_id(db: Session, post_id: int):
    return db.query(models.Post).filter(models.Post.post_id == post_id).first()

def get_posts_after_timestamp(db: Session, timestamp: date):
    return db.query(models.Post).filter(models.Post.timestamp > timestamp).all()

### GET QUESTIONS

def get_questions_by_template(db: Session, template_id: int):
    return db.query(models.Question).filter(models.Question.template_id == template_id).all()

def get_question(db: Session, question_id: int):
    return db.query(models.Question).filter(models.Question.question_id == question_id).first()

def get_check_in_questions(db: Session, this_check_in: int, this_template: int):
    return db.query(models.Question) \
        .filter(models.Question.template_id == this_template) \
        .filter(or_(models.Question.check_in_num == -1, models.Question.check_in_num == this_check_in)).all()    

### GET RESPONSES

def get_responses_by_goal(db: Session, goal_id: int):
    return db.query(models.Response).filter(models.Response.goal_id == goal_id).all()

def get_responses_by_question(db: Session, question_id: int):
    return db.query(models.Response).filter(models.Response.question_id == question_id).all()



###############################################################################

                        ### CR(U)D UPDATE METHODS ###

###############################################################################

def edit_comment(db: Session, comment_id, newcontent: str):
    comment = get_comment_by_id(db, comment_id)
    if comment:
        comment.content = newcontent
        db.commit()
        db.refresh(comment)
        return True
    return False

def edit_post_title(db: Session, post_id, newtitle: str):
    post = get_post_by_id(db, post_id)
    if post:
        post.title = newtitle
        db.commit()
        db.refresh(post)
        return True
    return False

def edit_post_content(db: Session, post_id, newcontent: str):
    post = get_post_by_id(db, post_id)
    if post:
        post.content = newcontent
        db.commit()
        db.refresh(post)
        return True
    return False

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

def update_can_check_in(db: Session):
    db.query(models.Goal).filter(models.Goal.is_paused == False) \
        .update({'can_check_in': models.Goal.next_check_in <= date.today()})
    db.commit()
    return "goals updated"

def toggle_goal_paused(db: Session, goal_id: int):
    goal = get_goal(db, goal_id)
    if goal:
        if goal.is_paused == True:
            goal.is_paused = False
            update_can_check_in(db=db)
            db.commit()
            return "Goal Unpaused"
        else:
            goal.is_paused = True
            goal.can_check_in = False
            db.commit()
            return "Goal Paused"
    else:
        return "Goal not found"                  

def after_check_in_update(goal_id: int, db: Session):
    goal = get_goal(db=db, goal_id=goal_id)
    db.query(models.Goal).filter(models.Goal.id == goal_id) \
        .update({'next_check_in': date.today() + timedelta(days=goal.check_in_period)}) \
    
    db.query(models.Goal).filter(models.Goal.id == goal_id) \
        .update({'check_in_num': models.Goal.check_in_num + 1})
    
    db.query(models.Goal).filter(models.Goal.id == goal_id) \
        .update({'can_check_in': False})
    
    db.commit()
    return



###############################################################################

                        ### CRU(D) DELETE METHODS ###

###############################################################################

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
        return True
    else:
        return False

def delete_comment(db: Session, comment_id: int):
    deleted=db.query(models.Comment).filter(models.Comment.comment_id == comment_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return True
    else:
        return False 

def delete_post(db: Session, post_id: int):
    deleted=db.query(models.Post).filter(models.Post.post_id == post_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return True
    else:
        return False