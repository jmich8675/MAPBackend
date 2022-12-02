import enum
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import date, timedelta, datetime
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
    db_post = models.Post(title=title, content=content, post_author=post_author, timestamp=datetime.now())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def create_comment(db: Session, content:str, post_id: int, comment_author: int):
    db_comment = models.Comment(content=content, timestamp=datetime.now(), post_id=post_id, comment_author=comment_author)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    update_recent_timestamp(db, post_id, db_comment.timestamp)
    return db_comment

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email, username=user.username,
                          pw_hash=user.pw_hash, pw_salt=user.pw_salt, verification_sent_date=date.today())
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

def create_friend_request(db: Session, user_id1: int, user_id2: int):
    db_friends = models.Friends(user1=user_id1, user2=user_id2)
    db.add(db_friends)
    db.commit()
    db.refresh(db_friends)
    return db_friends

###user_id is the creator of the group
def create_group(db: Session, name: str, user_id: int, template_id: int):
    db_group = models.Group(creator_id=user_id, group_name=name, template_id=template_id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    ###creator of a group should automatically be a member, so create invite, then accept invite
    create_group_invite(db=db, group_id=db_group.group_id, user_id=user_id)
    accept_group_invite(db=db, group_id=db_group.group_id, user_id=user_id)
    return db_group

def create_group_invite(db: Session, group_id: int, user_id: int):
    db_groupMember = models.GroupMembers(group_id=group_id, user_id=user_id)
    db.add(db_groupMember)
    db.commit()
    db.refresh(db_groupMember)
    return db_groupMember
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

def get_user_profile(db: Session, user_id: int):
    return db.query(models.User.username, models.User.email, models.User.id) \
    .filter(models.User.id==user_id).first()

def get_public_goals(db: Session, user_id: int):
    return db.query(models.Goal) \
        .filter(models.Goal.creator_id==user_id) \
        .filter(models.Goal.is_public==True).all()

def get_not_verified_users(db: Session):
    return db.query(models.User).filter(models.User.is_verified == False).all()


### GET GOALS

def get_goal(db: Session, goal_id: int):
    return db.query(models.Goal).filter(models.Goal.id == goal_id).first()

def get_user_goals(username: str, db: Session, skip: int = 0, limit: int = 100):
    user=db.query(models.User).filter(models.User.username == username).first()
    return user.goals

def get_user_goals_by_id(db: Session, user_id: int):
    return db.query(models.Goal).filter(models.Goal.creator_id == user_id).all()

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

### recent posts
def get_posts_after_timestamp(db: Session, timestamp: datetime):
    return db.query(models.Post).filter(models.Post.timestamp > timestamp).all()

def get_feed(db: Session, skip: int=0, limit: int=100):
    return db.query(models.Post).order_by(models.Post.timestamp.desc()) \
        .offset(skip).limit(limit).all()

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

### GET FRIENDS

def get_friendship(db: Session, user_id1: int, user_id2: int):
    friendship = db.query(models.Friends) \
        .filter(and_(models.Friends.user1==user_id2, models.Friends.user2==user_id1)).first()
    if not friendship:
        friendship = db.query(models.Friends) \
            .filter(and_(models.Friends.user1==user_id1, models.Friends.user2==user_id2)).first()
    return friendship

def accept_friend_request(db: Session, user_id1: int, user_id2: int):
    friendship = get_friendship(db=db, user_id1=user_id1, user_id2=user_id2)
    friendship.pending = False
    db.commit()
    db.refresh(friendship)
    return friendship

def deny_friend_request(db: Session, user_id1: int, user_id2: int):
    friendship = get_friendship(db=db, user_id1=user_id1, user_id2=user_id2)
    db.delete(friendship)
    db.commit()
    return "friendship ended"

def get_users_friends(db: Session, user_id: int):
    friends = []
    for friend in db.query(models.Friends).filter(models.Friends.user1==user_id) \
            .filter(models.Friends.pending == False).all():
        friends.append(friend.user2)
    for friend in db.query(models.Friends).filter(models.Friends.user2==user_id) \
            .filter(models.Friends.pending == False).all():
        friends.append(friend.user1)
    for i in range(len(friends)):
        friends[i] = get_user_profile(db=db, user_id=friends[i])
    return friends

def get_friend_requests(db: Session, user_id: int):
    friends = []
    for friend in db.query(models.Friends).filter(models.Friends.user2==user_id) \
            .filter(models.Friends.pending == True).all():
        friends.append(friend.user1)
    for i in range(len(friends)):
        friends[i] = get_user_profile(db=db, user_id=friends[i])
    return friends

def accept_group_invite(db: Session, group_id: int, user_id: int):
    membership = get_membership(db=db, group_id=group_id, user_id=user_id)
    membership.pending = False
    db.commit()
    db.refresh(membership)
    return membership

def deny_group_invite(db: Session, group_id: int, user_id: int):
    membership = get_membership(db=db, group_id=group_id, user_id=user_id)
    db.delete(membership)
    db.commit()
    return "membership denied"

def get_group(db: Session, group_id: int):
    return db.query(models.Group).filter(models.Group.group_id==group_id).first()

def get_membership(db: Session, group_id: int, user_id: int):
    return db.query(models.GroupMembers).filter(and_(models.GroupMembers.group_id==group_id, models.GroupMembers.user_id==user_id)).first()

def get_group_members(db: Session, group_id: int):
    members = []
    for member in db.query(models.GroupMembers).filter(models.GroupMembers.group_id==group_id).filter(models.GroupMembers.pending == False).all():
        members.append(member.user_id)
    
    for i in range(len(members)):
        members[i] = get_user_profile(db=db, user_id=members[i])

    return members    

def get_user_groups(db: Session, user_id: int):
    return db.query(models.GroupMembers).filter(models.GroupMembers.user_id==user_id).all()

def get_group_invites(db: Session, user_id: int):
    groups = []
    for group in db.query(models.GroupMembers).filter(models.GroupMembers.user_id==user_id).filter(models.GroupMembers.pending == True).all():
        groups.append(get_group(db=db, group_id=group.group_id)) 
    return groups

def get_template_by_creator(db: Session, creator_id: int):
    return db.query(models.Template).filter(models.Template.creator_id == creator_id).all()

###############################################################################

                        ### CR(U)D UPDATE METHODS ###

###############################################################################
def update_user_verification(db: Session, user_id: int):
    user = get_user(db, user_id)
    if user:
        user.is_verified = True
        db.commit()
        db.refresh(user)
        return True
    return False

def update_recent_timestamp (db: Session, post_id: int, timestamp: datetime):
    post = get_post_by_id(db, post_id)
    if post:
        post.recent_comment_timestamp = timestamp
        db.commit()
        db.refresh(post)
        return True ###post found, most recent comment timestamp updated
    return False ###post not found, most recent comment timestamp not updated

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
            db.commit()
            db.refresh(goal)
            update_can_check_in(db=db)
            return "Goal Unpaused"
        else:
            goal.is_paused = True
            goal.can_check_in = False
            db.commit()
            db.refresh(goal)
            return "Goal Paused"
    else:
        return "Goal not found"

def toggle_public_private(db: Session, goal_id: int):
    goal = get_goal(db, goal_id)
    if goal:
        if goal.is_public:
            goal.is_public = False
            db.commit()
            db.refresh(goal)
            return "Goal now private!"
        else:
            goal.is_public = True
            db.commit()
            db.refresh(goal)
            return "Goal now public!"
    else:
        return "Goal not found"

def change_verified_status(db: Session, user_id: int, is_verified: bool):
    user = get_user(db, user_id)
    if user:
        user.is_verified = is_verified
        db.commit()
        db.refresh(user)
        return "Account status updated"
    else:
        return "User not found"

def toggle_goal_private(db: Session, goal_id: int):
    goal = get_goal(db, goal_id)
    if goal:
        if goal.is_public == True:
            goal.is_public = False
            db.commit()
            db.refresh(goal)
            return "Goal set Private"
        else:
            goal.is_public = True
            db.commit()
            db.refresh(goal)
            return "Goal set Public"

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

def update_email_address(user_id: int, email: str, db: Session):
    user = get_user(db=db, user_id=user_id)
    user.email = email
    db.commit()

def update_email_address(user_id: int, email: str, db: Session):
    user = get_user(db=db, user_id=user_id)
    user.email = email
    db.commit()

def update_username(user_id: int, username: str, db: Session):
    user = get_user(db=db, user_id=user_id)
    user.username = username
    db.commit()

def update_password(user_id: int, newhash: str, newsalt: str, db: Session):
    user = get_user(db=db, user_id=user_id)
    if user:
        user.pw_hash = newhash
        user.pw_salt = newsalt
        db.commit()
        return True
    return False

###############################################################################

                        ### CRU(D) DELETE METHODS ###

###############################################################################

def delete_template(db: Session, template_id: int):
    
    for q in get_questions_by_template(db, template_id):
        delete_question(db, q.question_id)
    
    deleted = db.query(models.Template).filter(models.Template.template_id == template_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return True
    else:
        return False

def delete_question(db: Session, question_id: int):
    deleted = db.query(models.Question).filter(models.Question.question_id == question_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return True
    else:
        return False

def delete_response(db: Session, response_id: int):
    deleted = db.query(models.Response).filter(models.Response.response_id == response_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return True
    else:
        return False

def delete_all_user_friendships(db: Session, user_id: int):
    deleted1=db.query(models.Friends).filter(models.Friends.user1 == user_id).delete(synchronize_session="fetch")
    deleted2=db.query(models.Friends).filter(models.Friends.user2 == user_id).delete(synchronize_session="fetch")

    if deleted1 and deleted2:
        db.commit()
        return True
    else:
        return False

def delete_membership(db: Session, user_id: int):
    deleted=db.query(models.GroupMembers).filter(models.GroupMembers.user_id == user_id).delete(synchronize_session="fetch")

    if deleted:
        db.commit()
        return True
    else:
        return False

def delete_user(db: Session, user_id: int):

    ##delete all friendships featuring user
    delete_all_user_friendships(db, user_id)

    ##remove user from groups
    
    for g in get_user_groups(db, user_id):
        delete_membership(db, user_id)

    ##delete all posts by user, also deletes all comments associated with those posts
    for p in get_posts_by_author(db, user_id):
        delete_post(db, p.post_id)

    ##delete comments by user
    for c in get_comments_by_author(db, user_id):
        delete_comment(db, c.comment_id)

    ##delete all templates by user, also deletes all questions associated with those templates
    for t in get_template_by_creator(db, user_id):
        delete_template(db, t.template_id)
    
    ##delete all goals by user, also deletes all responses associated with those goals
    for g in get_user_goals_by_id(db, user_id):
        delete_goal(db, g.id)

    ##delete user
    deleted=db.query(models.User).filter(models.User.id == user_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return True
    else:
        return False

def delete_goal(db: Session, goal_id: int):
    for r in get_responses_by_goal(db, goal_id):
        delete_response(db, r.response_id)

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
    ### delete comments associated with the post
    for c in get_comments_by_post(db, post_id):
        delete_comment(db, c.comment_id)

    deleted=db.query(models.Post).filter(models.Post.post_id == post_id).delete(synchronize_session="fetch")
    if deleted:
        db.commit()
        return True
    else:
        return False

def delete_not_verified_users(db: Session):
    users = get_not_verified_users(db)
    for user in users:
        if ((date.today() - user.verification_sent_date) > timedelta(days=5)):
            delete_user(db, user.id)
