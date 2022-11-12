from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Enum, DateTime, Table, UniqueConstraint
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
    is_verified = Column(Boolean, default=False, index=True)

    goals = relationship("Goal", back_populates="creator")
    myposts = relationship("Post", back_populates="poster")
    #templates = relationsip("Template", back_populates="creator")

class Friends(Base):
    __tablename__ = "friends"

    user1 = Column(Integer, ForeignKey("users.id"), index=True, primary_key=True)
    user2 = Column(Integer, ForeignKey("users.id"), primary_key=True)
    pending = Column(Boolean, default=True)

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
    is_public = Column(Boolean, default=False)
    template_id = Column(Integer, index=True)
    is_achieved = Column(Boolean, default=False)
    can_check_in = Column(Boolean, default=False)

    creator = relationship("User", back_populates="goals")
    answers = relationship("Response", back_populates="goal", cascade="all, delete", passive_deletes=True)

class Template(Base):
    __tablename__ = "templates"

    template_id = Column(Integer, primary_key=True, index=True)
    is_custom = Column(Boolean, default=False)
    name = Column(String, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    #creator = relationship("User", back_populates="templates")
    questions = relationship("Question", back_populates="template")

class Question(Base):
    __tablename__ = "questions"

    question_id = Column(Integer, primary_key=True, index=True)
    text = Column(String, index=True)
    template_id = Column(Integer, ForeignKey("templates.template_id"))
    response_type = Column(Enum(response_types), index=True)
    check_in_num = Column(Integer, index=True)
    next_check_in_period = Column(Integer, index=True)

    template = relationship("Template", back_populates="questions")
    #answers = relationship("Response", back_populates="question")

class Response(Base):
    __tablename__ = "responses"

    response_id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.question_id"))
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"))
    text = Column(String, index=True)
    check_in_number = Column(Integer, index=True)

    #question = relationship("Question", back_populates="answers")
    goal = relationship("Goal", back_populates="answers")

class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String, index=True)
    post_author = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, index=True)
    recent_comment_timestamp = Column(DateTime, index=True, nullable=True)

    poster = relationship("User", back_populates="myposts")
    comments = relationship("Comment", backref="posts", cascade = "all, delete-orphan", passive_deletes=True)

class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True, index=True)
    content = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    post_id = Column(Integer, ForeignKey("posts.post_id", ondelete="CASCADE"))
    comment_author = Column(Integer, ForeignKey("users.id"))