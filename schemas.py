from datetime import date, datetime
from pydantic import BaseModel
import enum

class ResponseBase(BaseModel):
    text: str
    question_id: int 
    check_in_number: int
    goal_id: int 

class ResponseCreate(ResponseBase):
    pass

class Response(ResponseBase):
    response_id: int
    
    class Config:
        orm_mode = True

class QuestionBase(BaseModel):
    text: str
    response_type: enum.Enum

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    question_id: int
    template_id: int
    check_in_num: int
    next_check_in_period: int
    answers: list[Response] = []

    class Config:
        orm_mode = True

class TemplateBase(BaseModel):
    name: str
    is_custom: bool
    
class TemplateCreate(TemplateBase):
    pass

class Template(TemplateBase):
    template_id: int
    creator_id: int | None
    questions: list[Question] = []

    class Config:
        orm_mode = True

class GoalBase(BaseModel):
    goal_name: str
    next_check_in: date

class GoalSpecificCreate(GoalBase):
    template_id: int
    pass

class GoalCustomCreate(GoalBase):
    pass

class Goal(GoalBase):
    id: int
    creator_id: int
    is_paused: bool
    start_date: date
    check_in_period: int
    check_in_num: int
    is_public: bool
    is_achieved: bool
    can_check_in: bool
    answers: list[Response] = []

    class Config:
        orm_mode = True
    
class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    pw_hash: str
    pw_salt: str

class User(UserBase):
    id: int
    goals: list[Goal] = []
    templates: list[Template] = []
    is_verified: bool

    class Config:
        orm_mode = True

class FriendBase(BaseModel):
    user1_id: int
    user2_id: int

class FriendCreate(FriendBase):
    pass

class Friend(FriendBase):
    class Config:
        orm_mode = True

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    comment_id: int
    timestamp: datetime
    post_id: int
    comment_author: int
    
    class Config:
        orm_mode = True

class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    pass

class Post(PostBase):
    post_id: int
    post_author: int
    timestamp: datetime
    recent_comment_timestamp: datetime
    poster: User
    comments: list[Comment] = []

    class Config:
        orm_mode = True