from datetime import date, timedelta
from pydantic import BaseModel
import enum

from sqlalchemy import Integer, Interval

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


class TemplateBase(BaseModel):
    name: str
    is_custom: bool
    
class TemplateCreate(TemplateBase):
    pass

class Template(TemplateBase):
    template_id: int
    creator_id: int
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
    check_in_period: timedelta
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
    pw_salt: str

class User(UserBase):
    id: int
    goals: list[Goal] = []
    templates: list[Template] = []

    class Config:
        orm_mode = True

