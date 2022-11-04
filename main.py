from email import header
import re
from typing import Union
from urllib import request
from fastapi import FastAPI, Response, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette.responses import RedirectResponse, JSONResponse
import starlette.status as status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware import Middleware
from jose import JWTError, jwt
from datetime import date, datetime, timedelta
from functools import wraps
import bcrypt
from fastapi.routing import APIRoute
from fastapi.exceptions import RequestValidationError

# DATABASE
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
import crud, models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# DATABASE
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class TokenData(BaseModel):
    username: Union[str, None] = None


# REQUEST MODELS
class User(BaseModel):
    email: str | None = None
    username: str
    password: str


# REQUEST MODELS

# JWT STUFF
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# returns current user as a models.User object
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username)

    if user is None:
        raise credentials_exception
    print(type(user))
    return user


origins = [
    "http://localhost:3000"
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
]

app = FastAPI(middleware=middleware)


# CORS STUFF

@app.get("/")
def root():
    return {"message": "Welcome to MAP website"}


@app.post("/signup")
def signup(user: User, response: Response, db: Session = Depends(get_db)):
    print(f"signup {user.username} {user.email} {user.password}")

    # check the db to see if user with this email exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        message = {"message": "User with the email already exists"}
        response.status_code = status.HTTP_302_FOUND
        return message

    # check the db to see if user with this username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        message = {"message": "User with the username already exists"}
        response.status_code = status.HTTP_302_FOUND
        return message

    # IS A NEW USER

    # generate a salt
    salt = bcrypt.gensalt(12)
    # combine and generate the pass hash
    passhash = bcrypt.hashpw(user.password.encode('utf-8'), salt)
    salt = salt.decode('utf-8')
    passhash = passhash.decode('utf-8')
    print(f"{salt} {passhash}")

    # make a schema
    new_user = schemas.UserCreate(email=user.email, username=user.username,
                                  pw_hash=passhash, pw_salt=salt)
    new_user = crud.create_user(db, new_user)

    # if not successful database transaction
    if not new_user:
        message = {"message": "Error Occurred while creating the user"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message

    message = {"message": "User created Successfully",
               "username": user.username,
               "token_type": "Bearer"}
    response.status_code = status.HTTP_200_OK
    return message


def verify_password(plain_password, hashed_password):
    print("Plain Password:")
    print(plain_password)
    print(type(plain_password))
    print("Hashed Password:")
    print(hashed_password)
    print(type(hashed_password))

    print("Encoded Plain Password:")
    print(plain_password.encode('utf8'))
    print(type(plain_password.encode('utf8')))

    return bcrypt.checkpw(plain_password.encode('utf8'), hashed_password.encode('utf8'))


def authenticate_user(db, username: str, password: str):
    user = crud.get_user_by_username(db, username)
    print(user.pw_hash)

    if not user:
        print(not user)
        return False
    if not verify_password(password, user.pw_hash):
        print("failed to verify")
        return False
    return user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


#
# @app.post("/login")
# def login(user: User, response: Response, db: Session = Depends(get_db)):
#     print(f"login {user.username} {user.password}")
#
#     # check the db to see if user with this username does not exist
#     db_user = crud.get_user_by_username(db, username=user.username)
#     if not db_user:
#         message = {"message": "user with the username does not exist"}
#         response.status_code = status.HTTP_403_FORBIDDEN
#         return message
#
#     # IS A RETURNING USER
#
#     # see if the given password match with the password in db
#     db_passhash = bytes(db_user.pw_hash, 'utf-8')
#     salt = bytes(db_user.pw_salt, 'utf-8')
#     curr_passhash = bcrypt.hashpw(user.password.encode('utf-8'), salt)
#
#     print(f"{salt} {db_passhash} {curr_passhash}")
#     # verify password
#     if db_passhash != curr_passhash:
#         message = {"message": "Incorrect Password"}
#         response.status_code = status.HTTP_403_FORBIDDEN
#         return message
#
#     # is the correct user
#     # generate JWT token and send it as header along with the 200 ok status
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.username}, expires_delta=access_token_expires
#     )
#     message = {"message": "User logged in successfully",
#                "username": user.username,
#                "access_token": access_token,
#                "token_type": "bearer"}
#     response.status_code = status.HTTP_200_OK
#     return message

@app.get("/goals")
def home(db: Session = Depends(get_db),
         current_user: models.User = Depends(get_current_user)):
    return {"message": crud.get_user_goals(db=db, username=current_user.username)}


class SmallResponse(BaseModel):
    text: str
    question_id: int


class BigGoal(BaseModel):
    goal_name: str
    template_id: int
    check_in_period: int
    responses: list[SmallResponse] = []


# Refactored
@app.post("/create_specific_goal")
def create_specific_goal(goaljson: BigGoal,
                         response: Response,
                         db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    template = crud.get_template(db=db, template_id=goaljson.template_id)
    if not template:
        message = {"message": "template does not exist"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message

    goal = crud.create_goal(db=db, goal_name=goaljson.goal_name,
                            check_in_period=goaljson.check_in_period,
                            template_id=goaljson.template_id,
                            user_id=current_user.id)

    for answer in goaljson.responses:
        question = crud.get_question(db=db, question_id=answer.question_id)
        if not question:
            message = {"message": "question does not exist"}
            response.status_code = status.HTTP_400_BAD_REQUEST
            return message

        crud.create_response(db=db, text=answer.text, question_id=answer.question_id,
                             check_in_number=0, goal_id=goal.id)
    message = {"goal and responses created successfully!"}
    response.status_code = status.HTTP_201_CREATED
    return message


class BigCustomGoal(BaseModel):
    goal_name: str
    check_in_period: int
    questions_answers: list[list[str, str]] = []


# Refactored
@app.post("/create_custom_goal")
def create_custom_goal(goal_json: BigCustomGoal,
                       response: Response,
                       db: Session = Depends(get_db),
                       current_user: models.User = Depends(get_current_user)):
    template = crud.create_template(db=db, name=goal_json.goal_name, is_custom=True,
                                    creator_id=current_user.id)
    if not template:
        message = {"message": "template not created"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message

    goal = crud.create_goal(db=db, goal_name=goal_json.goal_name, check_in_period=goal_json.check_in_period,
                            template_id=template.template_id, user_id=current_user.id)
    if not goal:
        message = {"message": "goal not created"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message

    for QA in goal_json.questions_answers:
        question = crud.create_question(db=db, text=QA[0], template_id=template.template_id,
                                        response_type=models.response_types(0), next_check_in_period=0)
        answer = crud.create_response(db=db, text=QA[1], question_id=question.question_id,
                                      check_in_number=0, goal_id=goal.id)

    message = {"custom goal created!"}
    response.status_code = status.HTTP_201_CREATED
    return message


# Refactored
@app.post("/create_template")
def create_template(template: schemas.TemplateCreate,
                    response: Response,
                    db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    creator_id = current_user.id
    crud.create_template(db=db, name=template.name, is_custom=template.is_custom,
                         creator_id=creator_id)
    message = {"message": "template successfully created!"}
    return message


class GoalInfo(BaseModel):
    name: str
    start_date: date
    check_in_period: int
    next_check_in: date


# Refactored
@app.get("/progress/{goal_id}")
def view_goal_progress(goal_id: int,
                       response: Response,
                       db: Session = Depends(get_db),
                       current_user: models.User = Depends(get_current_user)):
    goal = crud.get_goal(db=db, goal_id=goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_404_NOT_FOUND
        return message
    if goal.creator_id != current_user.id:
        message = {"message": "not your goal"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message
    message = {
        "name": goal.goal_name,
        "start_date": goal.start_date,
        "check_in_period": goal.check_in_period,
        "next_check_in": goal.next_check_in,
        "is_achieved": goal.is_achieved
    }
    return message


@app.get("/templates", response_model=list[schemas.Template])
def view_premade_templates(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return crud.get_premade_templates(db=db, skip=skip, limit=limit)


class PastWriting(BaseModel):
    question: str
    answer: str
    check_in_number: int


# Refactored
@app.get("/responses/{goal_id}")
def view_responses(goal_id: int,
                   response: Response,
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    goal = crud.get_goal(db=db, goal_id=goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_404_NOT_FOUND
        return message
    if goal.creator_id != current_user.id:
        message = {"message": "not your goal"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message
    writings = []
    answers = crud.get_responses_by_goal(db=db, goal_id=goal_id)
    for answer in answers:
        question = crud.get_question(db=db, question_id=answer.question_id)
        writing = PastWriting(
            question=question.text,
            answer=answer.text,
            check_in_number=answer.check_in_number
        )
        writings.append(writing)
    return writings


# Refactored
@app.post("/create_response")
def create_response(resp: schemas.ResponseCreate,
                    response: Response,
                    db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    goal = crud.get_goal(db=db, goal_id=resp.goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_404_NOT_FOUND
        return message
    if goal.creator_id != current_user.id:
        message = {"message": "not your goal"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message
    crud.create_response(db=db, response=resp)
    message = {"message": "response created!"}
    return message


# Refactored
@app.put("/achieved_goal/{goal_id}")
def achieved_goal(goal_id: int,
                  response: Response,
                  db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    goal = crud.get_goal(db=db, goal_id=goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_404_NOT_FOUND
        return message
    if goal.creator_id != current_user.id:
        message = {"message": "not your goal"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message
    if not crud.mark_goal_achieved(db=db, goal_id=goal_id):
        message = {"message": "some server error?!"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message
    message = {"message": "goal achieved! congrats!"}
    response.status_code = status.HTTP_200_OK
    return message


# Refactored
@app.delete("/delete_goal/{goal_id}/")
def delete_goal(username: str,
                goal_id: int,
                response: Response,
                db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    goal = crud.get_goal(db=db, goal_id=goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_404_NOT_FOUND
        return message
    if goal.creator_id != current_user.id:
        message = {"message": "not your goal"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message
    if not crud.delete_goal(db=db, goal_id=goal_id):
        message = {"message": "goal not deleted"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message
    message = {"message": "goal deleted!"}
    response.status_code = status.HTTP_200_OK
    return message


class CheckInPeriod(BaseModel):
    new_check_in: int


# Refactored
@app.put("/edit_check_in_period/{goal_id}")
def edit_check_in_period(goal_id: int,
                         check_in_period: CheckInPeriod,
                         response: Response,
                         db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    goal = crud.get_goal(db=db, goal_id=goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_404_NOT_FOUND
        return message
    if goal.creator_id != current_user.id:
        message = {"message": "not your goal"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message
    if not crud.update_goal_check_in_period(db=db, goal_id=goal_id, new_check_in=check_in_period.new_check_in):
        message = {"message": "server error"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message
    message = {"message": "check in period updated!"}
    response.status_code = status.HTTP_200_OK
    return message


# test route for login system

@app.get("/users/me/")
async def read_users_me(
        current_user: models.User = Depends(get_current_user)):
    return {"username": current_user.username}


@app.get("/users/me/email")
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {"email": current_user.email}
