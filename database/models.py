from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship

from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    pw_hash = Column(String)
    pw_salt = Column(String)
    email = Column(String, unique=True, index=True)

    goals = relationship("Goal", back_populates="creator")

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    goal_name = Column(String, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    is_paused = Column(Boolean, default=False)
    start_date = Column(Date, index=True)
    check_in_period = Column(Integer, index=True)
    next_check_in = Column(Date, index=True)
    check_in_num = Column(Integer, index=True)
    is_public = Column(Boolean)

    creator = relationship("User", back_populates="goals")
    
