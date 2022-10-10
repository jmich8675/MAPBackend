from sqlalchemy import Boolean, Column, ForeignKey, Integer, Interval, String, Date, Enum
from sqlalchemy.orm import relationship
import enum
from database import Base

class response_types(enum.Enum):
    TYPE = 0
    SELECT = 1

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    pw_hash = Column(String)
    pw_salt = Column(String)
    email = Column(String, unique=True, index=True)

    goals = relationship("Goal", back_populates="creator")
    templates = relationship("Template", back_populates="creator")

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    goal_name = Column(String, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    is_paused = Column(Boolean, default=False)
    start_date = Column(Date, index=True)
    check_in_period = Column(Interval, index=True)
    next_check_in = Column(Date, index=True)
    check_in_num = Column(Integer, index=True)
    is_public = Column(Boolean)

    creator = relationship("User", back_populates="goals")
    answers = relationship("Response", back_populates="goal")

class Template(Base):
    __tablename__ = "templates"

    template_id = Column(Integer, primary_key=True, index=True)
    is_custom = Column(Boolean, default=False)
    name = Column(String, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), default=-1)

    creator = relationship("User", back_populates="templates")
    questions = relationship("Question", back_populates="template")

class Question(Base):
    __tablename__ = "questions"

    question_id = Column(Integer, primary_key=True, index=True)
    text = Column(String, index=True)
    template_id = Column(Integer, ForeignKey("templates.template_id"))
    response_type = Column(Enum(response_types), index=True)
    check_in_num = Column(Integer, index=True)
    next_check_in_period = Column(Interval, index=True)

    template = relationship("Template", back_populates="questions")
    answers = relationship("Response", back_populates="question")

class Response(Base):
    __tablename__ = "responses"

    response_id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.question_id"))
    goal_id = Column(Integer, ForeignKey("goals.id"))
    text = Column(String, index=True)
    check_in_number = Column(Integer, index=True)

    question = relationship("Question", back_populates="answers")
    goal = relationship("Goal", back_populates="answers")
    