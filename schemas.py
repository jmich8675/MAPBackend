from datetime import date, timedelta
from pydantic import BaseModel
import enum

from sqlalchemy import Integer, Interval

class TemplateBase(BaseModel):
    name: str
    
class TemplateCreate(TemplateBase):
    pass

class Template(TemplateBase):
    is_custom: bool
    template_id: int
    creator_id: int

    class Config:
        orm_mode = True

class ResponseBase(BaseModel):
    text: str
    question_id: int
    goal_id: int
    check_in_number = int

class ResponseCreate(ResponseBase):
    pass

class Response(ResponseBase):
    response_id: int
    
    class Config:
        orm_mode = True

class GoalBase(BaseModel):
    goal_name: str
    check_in_period: timedelta

class GoalCreate(GoalBase):
    pass

class Goal(GoalBase):
    id: int
    creator_id: int
    is_paused: bool
    start_date: date
    next_check_in: date
    check_in_num: int
    is_public: bool
    answers: list[Response] = []

    class Config:
        orm_mode = True
    
class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    pw_hash: str
    pw_salt: int

class User(UserBase):
    id: int
    goals: list[Goal] = []
    templates: list[Template] = []

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
    next_check_in_period: timedelta
    answers: list[Response] = []

    class Config:
        orm_mode = True
