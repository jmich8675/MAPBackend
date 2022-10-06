from datetime import date
from pydantic import BaseModel


class GoalBase(BaseModel):
    goal_name: str
    check_in_period: int

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

    class Config:
        orm_mode = True
    

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    goals: list[Goal] = []

    class Config:
        orm_mode = True

