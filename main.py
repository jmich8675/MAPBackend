from utiltity import measure_time, is_email
from typing import Union
from fastapi import FastAPI, Response, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette.responses import RedirectResponse, JSONResponse
import starlette.status as status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware import Middleware
from jose import JWTError, jwt
from datetime import date, datetime, timedelta
from functools import wraps
import bcrypt
from fastapi.routing import APIRoute
import exceptions
from database import get_database
from email_sender import emailVerification

# DATABASE
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
import crud, models, schemas
from database import engine

models.Base.metadata.create_all(bind=engine)

Base2 = models.Base


def get_db():
    return next(get_database())


def is_running_tests():
    return False


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
ACCESS_TOKEN_EXPIRE_MINUTES = 60
ACCESS_TOKEN_EXPIRE_DAYS = 5


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


# method used to be async
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        type_payload: str = payload.get("typ")
        if type_payload is None:
            raise credentials_exception
        if type_payload != "auth":
            raise credentials_exception
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username)

    if user is None:
        raise credentials_exception
    return user


def verify_access_token(token: str, username: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username_payload: str = payload.get("sub")
        type_payload: str = payload.get("typ")
        if type_payload is None:
            return False
        if type_payload != "auth":
            return False
        if username_payload is None:
            return False
        if username_payload != username:
            return False
    except JWTError:
        return False
    return True


# JWT STUFF
# CORS STUFF
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


# app.router.route_class = IsLoggedIn


# CORS STUFF

@app.get("/")
@measure_time
def root():
    return {"message": "Welcome to MAP website"}


# trying post request
@app.post("/signup")
@measure_time
def signup(user: User, response: Response, db: Session = Depends(get_db),
           skip_for_testing: bool = Depends(is_running_tests)):
    # print(f"signup {user.username} {user.email} {user.password}")
    # check if valid email address
    if not is_email(user.email):
        message = {"message": "Please enter a valid Email"}
        response.status_code = status.HTTP_406_NOT_ACCEPTABLE
        return message

    # check the db to see if user with this email exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        message = {"message": "User with the email already exists"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message

    # check the db to see if user with this username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        message = {"message": "User with the username already exists"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message

    # IS A NEW USER

    # generate a salt
    salt = bcrypt.gensalt(12)
    # combine and generate the pass hash
    passhash = bcrypt.hashpw(user.password.encode('utf-8'), salt)
    salt = salt.decode('utf-8')
    passhash = passhash.decode('utf-8')
    # print(f"{salt} {passhash}")

    # make a schema
    new_user = schemas.UserCreate(email=user.email, username=user.username,
                                  pw_hash=passhash, pw_salt=salt)
    new_user = crud.create_user(db, new_user)

    # if not successful database transaction
    if not new_user:
        message = {"message": "Error Occurred while creating the user"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message

    # generate JWT token for email verification
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    #sub has to be string
    access_token = create_access_token(
        data = {"sub": str({ 
                        "user" : new_user.username, 
                        "id": new_user.id
        }),
        "typ": "email_verification"
        }
        , expires_delta=access_token_expires
    )
    if skip_for_testing or len(new_user.username) == 1:
        crud.change_verified_status(db=db, user_id=new_user.id, is_verified=True)
    else:
        # send the email verification
        sent = emailVerification(email=user.email, user=user.username, token=access_token)

        if not sent:
            # delete the created user
            crud.delete_user(db=db, user_id=new_user.id)
            message = {"message": "Error Occurred while creating the user"}
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return message

    # if email send and user created.

    message = {"message": "User created Successfully, Please verify your email",
               "username": new_user.username,
               "user_id": new_user.id}
    response.status_code = status.HTTP_200_OK
    return message

@app.get("/verify_email/")
@measure_time
def verify_email(q: str, response: Response, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token=q, key=SECRET_KEY, algorithms=[ALGORITHM])
        sub_payload:str = payload.get("sub")
        # convert string back to dict to retrieve user and user_id
        sub_payload:dict = eval(sub_payload)
        type_payload: str = payload.get("typ")
        
        if type_payload == None:
            message = {"message": "Bad credentials/type"}
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return message

        if type_payload != "email_verification":
            message = {"message": "Bad credentials/type_not_email_token"}
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return message

        user: str = sub_payload.get("user")
        user_id: int = sub_payload.get("id")
        
        db_user = crud.get_user(db, user_id)

        if not db_user:
            message = {"message": "Bad credentials/user"}
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return message
        
        if db_user.username != user:
            message = {"message": "Bad credentials/username"}
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return message
        
        if db_user.is_verified:
            message = {"message": "User Email already verified"}
            response.status_code = status.HTTP_200_OK
            return message
        
        if not crud.update_user_verification(db, db_user.id):
            message = {"message": "Error updating verification"}
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return message
        
        message = {"message": "Succesfully verified your Email"}
        response.status_code = status.HTTP_200_OK
        return message
        
    except JWTError:
        message = {"message": "Bad credentials/tokendecode"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message
    


def verify_password(plain_password, hashed_password):

    return bcrypt.checkpw(plain_password.encode('utf8'), hashed_password.encode('utf8'))


def authenticate_user(db, username: str, password: str):
    user = crud.get_user_by_username(db, username)
    # print(user.pw_hash)

    if not user:
        print(not user)
        return False
    if not verify_password(password, user.pw_hash):
        # print("failed to verify")
        return False
    return user


# this function used to be async
@app.post("/token", response_model=Token)
@measure_time
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please verify your account in your email!",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": user.username, "typ": "auth"}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


def verify_username_and_goal(username: str, goal_id: int, response: Response,
                             db: Session):
    user = crud.get_user_by_username(db=db, username=username)
    goal = crud.get_goal(db=db, goal_id=goal_id)
    if not goal:
        raise exceptions.NonexistentGoalException
    if goal.creator_id != user.id:
        raise exceptions.ForbiddenGoalException


def verify_username_and_post(username: str, post_id: int, response: Response,
                             db: Session):
    user = crud.get_user_by_username(db=db, username=username)
    post = crud.get_post_by_id(db=db, post_id=post_id)
    if not post:
        raise exceptions.NonexistentForumPostException
    if post.post_author != user.id:
        raise exceptions.ForbiddenForumPostException
    return True


@app.get("/user/me")
@measure_time
def home(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return {"username": current_user.username}


@app.get("/goals")
@measure_time
def home(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return {"message": crud.get_unachieved_goals(db=db, username=current_user.username)}


class SmallResponse(BaseModel):
    text: str
    question_id: int


class BigGoal(BaseModel):
    goal_name: str
    template_id: int
    check_in_period: int
    responses: list[SmallResponse] = []


@app.post("/create_specific_goal")
@measure_time
def create_specific_goal(goaljson: BigGoal, response: Response, db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    user = crud.get_user_by_username(db=db, username=current_user.username)
    if not user:
        message = {"message": "user does not exist"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message
    template = crud.get_template(db=db, template_id=goaljson.template_id)
    if not template:
        message = {"message": "template does not exist"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message

    goal = crud.create_goal(db=db, goal_name=goaljson.goal_name,
                            check_in_period=goaljson.check_in_period,
                            template_id=goaljson.template_id,
                            user_id=user.id)

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


@app.post("/create_custom_goal")
@measure_time
def create_custom_goal(goaljson: BigCustomGoal,
                       response: Response, db: Session = Depends(get_db),
                       current_user: models.User = Depends(get_current_user)):
    # print(goaljson.questions_answers)
    if not current_user:
        message = {"message": "user not found"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message

    template = crud.create_template(db=db, name=goaljson.goal_name, is_custom=True,
                                    creator_id=current_user.id)
    if not template:
        message = {"message": "template not created"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message

    goal = crud.create_goal(db=db, goal_name=goaljson.goal_name, check_in_period=goaljson.check_in_period,
                            template_id=template.template_id, user_id=current_user.id)
    if not goal:
        message = {"message": "goal not created"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message

    for QA in goaljson.questions_answers:
        question = crud.create_question(db=db, text=QA[0], template_id=template.template_id,
                                        response_type=models.response_types(0), next_check_in_period=0)
        answer = crud.create_response(db=db, text=QA[1], question_id=question.question_id,
                                      check_in_number=0, goal_id=goal.id)

    message = {"message": "custom goal created!",
               "goal_id": goal.id,
               "template_id": template.template_id,
               "creator_id": current_user.id}
    response.status_code = status.HTTP_201_CREATED
    return message


@app.post("/create_template")
@measure_time
def create_template(template: schemas.TemplateCreate,
                    response: Response, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    if not current_user:
        message = {"message": "error: user not found"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message
    creator_id = current_user.id
    template = crud.create_template(db=db, name=template.name, is_custom=template.is_custom,
                                    creator_id=creator_id)
    message = {"message": "template successfully created!",
               "template_id": template.template_id}
    return message


class GoalInfo(BaseModel):
    name: str
    start_date: date
    check_in_period: int
    next_check_in: date


@app.get("/progress/{goal_id}")
@measure_time
def view_goal_progress(goal_id: int, response: Response, db: Session = Depends(get_db),
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
        "is_achieved": goal.is_achieved,
        "is_paused": goal.is_paused,
        "is_public": goal.is_public
    }
    return message


@app.get("/templates", response_model=list[schemas.Template])
@measure_time
def view_premade_templates(db: Session = Depends(get_db), skip: int = 0, limit: int = 100,
                           current_user: models.User = Depends(get_current_user)):
    return crud.get_premade_templates(db=db, skip=skip, limit=limit)


class PastWriting(BaseModel):
    question: str
    answer: str
    check_in_number: int


# might be unsecure
@app.get("/responses/{goal_id}")
@measure_time
def view_responses(goal_id: int, response: Response, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    verify_username_and_goal(username=current_user.username, goal_id=goal_id, db=db, response=response)
    goal = crud.get_goal(db=db, goal_id=goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_404_NOT_FOUND
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


# might be unsecure
@app.post("/create_response")
@measure_time
def create_response(resp: schemas.ResponseCreate, response: Response,
                    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    goal = crud.get_goal(db=db, goal_id=resp.goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message
    crud.create_response(db=db, response=resp)
    message = {"message": "response created!"}
    return message


@app.put("/achieved_goal/{goal_id}")
@measure_time
def achieved_goal(goal_id: int, response: Response, db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    verify_username_and_goal(username=current_user.username, goal_id=goal_id, db=db, response=response)
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


@app.delete("/delete_goal/{goal_id}")
@measure_time
def delete_goal(goal_id: int, response: Response, db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    verify_username_and_goal(username=current_user.username, goal_id=goal_id, db=db, response=response)
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


@app.put("/edit_check_in_period/{goal_id}")
@measure_time
def edit_check_in_period(goal_id: int, check_in_period: CheckInPeriod,
                         response: Response, db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    verify_username_and_goal(username=current_user.username, goal_id=goal_id, db=db, response=response)
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


@app.put("/update_database")
@measure_time
def update_database(response: Response, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    crud.update_can_check_in(db=db)
    message = {"message": "database updated"}
    response.status_code = status.HTTP_200_OK
    return message


@app.get("/list_check_in_questions/{goal_id}")
@measure_time
def list_check_in_questions(goal_id: int, response: Response, db: Session = Depends(get_db),
                            current_user: models.User = Depends(get_current_user)):
    verify_username_and_goal(username=current_user.username, goal_id=goal_id, db=db, response=response)
    # error checking
    goal = crud.get_goal(db=db, goal_id=goal_id)
    return crud.get_check_in_questions(db=db, this_check_in=goal.check_in_num + 1, this_template=goal.template_id)


class CheckInAnswers(BaseModel):
    answers: list[SmallResponse] = []


@app.post("/check_in/{goal_id}")
@measure_time
def check_in(goal_id: int, check_in_answers: CheckInAnswers,
             response: Response, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    verify_username_and_goal(username=current_user.username, goal_id=goal_id, db=db, response=response)
    goal = crud.get_goal(db=db, goal_id=goal_id)
    for answer in check_in_answers.answers:
        question = crud.get_question(db=db, question_id=answer.question_id)
        if not question:
            message = {"message": "question does not exist"}
            response.status_code = status.HTTP_400_BAD_REQUEST
            return message

        crud.create_response(db=db, text=answer.text, question_id=answer.question_id,
                             check_in_number=goal.check_in_num + 1, goal_id=goal.id)
    crud.after_check_in_update(goal_id=goal_id, db=db)
    message = {"answers created successfully!"}
    response.status_code = status.HTTP_201_CREATED
    return message


@app.put("/togglepause/{goal_id}")
@measure_time
def togglepause(goal_id: int, response: Response, db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    verify_username_and_goal(username=current_user.username, goal_id=goal_id, db=db, response=response)
    crud.toggle_goal_paused(db=db, goal_id=goal_id)
    message = {"message": "Pause Toggled!"}
    response.status_code = status.HTTP_200_OK
    return message


@app.get("/achieved_goals")
@measure_time
def achieved_goals(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_achieved_goals(username=current_user.username, db=db)


class PostInfo(BaseModel):
    title: str
    content: str


@app.post("/create_post")
@measure_time
def create_post(postjson: PostInfo, response: Response, db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    post = crud.create_post(db=db, title=postjson.title, content=postjson.content, post_author=current_user.id)
    message = {"message": "Post Created!",
               "post_id": post.post_id}
    response.status_code = status.HTTP_201_CREATED
    return message


@app.get("/see_posts", response_model=list[schemas.Post])
@measure_time
def get_posts(db: Session = Depends(get_db), skip: int = 0, limit: int = 100,
              current_user: models.User = Depends(get_current_user)):
    return crud.get_feed(db=db, skip=skip, limit=limit)


class EditPost(BaseModel):
    content: str


@app.put("/edit_post/{post_id}")
@measure_time
def edit_post(post_id: int, editjson: EditPost,
              response: Response, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    verify_username_and_post(username=current_user.username, post_id=post_id,
                             response=response, db=db)
    result = crud.edit_post_content(db=db, post_id=post_id,
                                    newcontent=editjson.content)
    if result:
        message = {"Successfully Edited!"}
        response.status_code = status.HTTP_200_OK
    else:
        message = {"Edit Failed!"}
        response.status_code = status.HTTP_400_BAD_REQUEST
    return message


class Commment(BaseModel):
    text: str


@app.post("/leave_comment/{post_id}")
@measure_time
def leave_comment(post_id: int, comment: Commment, db: Session = Depends(get_db),
                  current_user: models.User = Depends(get_current_user)):
    if not current_user:
        raise exceptions.NonexistentUserException
    post = crud.get_post_by_id(db=db, post_id=post_id)
    if not post:
        raise exceptions.NonexistentForumPostException
    comment = crud.create_comment(db=db, content=comment.text, post_id=post_id, comment_author=current_user.id)
    message = {"message": "comment created!",
               "comment_id": comment.comment_id}
    return message


class comments_with_author(BaseModel):
    comment_id: int
    content: str
    timestamp: datetime
    post_id: int
    comment_author: int
    author_username: str


@app.get("/comments/{post_id}")
@measure_time
def see_comments(post_id: int, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    real_comments = []
    comments = crud.get_comments_by_post(db=db, post_id=post_id)
    for i in range(len(comments)):
        real_comments.append(comments_with_author(
            comment_id=comments[i].comment_id,
            content=comments[i].content,
            timestamp=comments[i].timestamp,
            post_id=comments[i].post_id,
            comment_author=comments[i].comment_author,
            author_username=crud.get_user(db=db, user_id=comments[i].comment_author).username
        ))
    return real_comments


class Peers(BaseModel):
    user_id1: int
    user_id2: int


@app.post("/send_friend_request/{username}")
@measure_time
def send_friend_request(username: str, response: Response, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    user1 = current_user
    user2 = crud.get_user_by_username(db=db, username=username)
    if not user1 or not user2:
        raise exceptions.NonexistentUserException
    if user1.id == user2.id:
        raise exceptions.SelfFriendRequestException
    friendship = crud.get_friendship(db=db, user_id1=user1.id, user_id2=user2.id)
    if friendship:
        if friendship.pending:
            raise exceptions.AlreadySentFriendRequestException
        else:
            raise exceptions.AlreadyFriendsException
    crud.create_friend_request(db=db, user_id1=current_user.id, user_id2=user2.id)
    message = {"detail": "Friend Request sent"}
    return message


@app.get("/my_friend_requests")
@measure_time
def see_friend_requests(db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    return crud.get_friend_requests(db=db, user_id=current_user.id)


@app.post("/accept_friend_request/{username}")
def accept_friend_request(username: str, response: Response, db: Session = Depends(get_db),
                          current_user: models.User = Depends(get_current_user)):
    user1 = current_user
    user2 = crud.get_user_by_username(db=db, username=username)
    if not user1 or not user2:
        raise exceptions.NonexistentUserException
    friendship = crud.get_friendship(db=db, user_id1=user1.id, user_id2=user2.id)
    if not friendship:
        raise exceptions.FriendRequestDoesNotExistException
    if not friendship.pending:
        raise exceptions.AlreadyFriendsException
    crud.accept_friend_request(db=db, user_id1=user1.id, user_id2=user2.id)
    message = {"detail": "friendship accepted"}
    return message


@app.post("/deny_friend_request/{username}")
@measure_time
def deny_friend_requesst(username: str, response: Response, db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    user1 = current_user
    user2 = crud.get_user_by_username(db=db, username=username)
    if not user1 or not user2:
        raise exceptions.NonexistentUserException
    friendship = crud.get_friendship(db=db, user_id1=user1.id, user_id2=user2.id)
    if not friendship:
        raise exceptions.FriendRequestDoesNotExistException

    if not friendship.pending:
        raise exceptions.AlreadyFriendsException
    crud.deny_friend_request(db=db, user_id1=user1.id, user_id2=user2.id)
    message = {"detail": "friendship denied successfully"}
    return message


@app.get("/friends")
@measure_time
def my_friends(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_users_friends(db=db, user_id=current_user.id)


@app.get("/public_goals/{user_id}")
def public_goals(user_id: int, db: Session = Depends(get_db)):
    return crud.get_public_goals(db=db, user_id=user_id)


@app.put("/togglepublic/{goal_id}")
@measure_time
def togglepublic(goal_id: int, response: Response, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    verify_username_and_goal(username=current_user.username, goal_id=goal_id, db=db, response=response)
    return crud.toggle_public_private(db=db, goal_id=goal_id)


# SETTINGS

class NewEmail(BaseModel):
    email: str


@app.put("/change_email_address")
def change_email_address(emailjson: NewEmail, db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    crud.update_email_address(user_id=current_user.id, email=emailjson.email, db=db)
    message = {"email updated"}
    return message


class NewUsername(BaseModel):
    username: str


@app.put("/change_username")
def change_username(json: NewUsername, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    crud.update_username(user_id=current_user.id, username=json.username, db=db)
    message = {"username updated"}
    return message
    # make sure to logout


class NewPassword(BaseModel):
    repw: str
    newpw: str


@app.put("/change_password")
def change_password(pwjson: NewPassword, response: Response, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    if not verify_password(pwjson.repw, current_user.pw_hash):
        message = {"passwords do not match!"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message
    salt = bcrypt.gensalt(12)
    passhash = bcrypt.hashpw(pwjson.newpw.encode('utf-8'), salt)
    salt = salt.decode('utf-8')
    passhash = passhash.decode('utf-8')
    crud.update_password(user_id=current_user.id, newhash=passhash, newsalt=salt, db=db)
    message = {"password updated"}
    return message

#@app.get("/{username}/profile")
#def view_profile():
    #view profile, no verification

class GoalNGroupInfo(BigGoal):
    group_name: str
    invites: list[str]

@app.post("/create_specific_goal_and_group")
def create_specific_goal_and_group(json: GoalNGroupInfo, response: Response, db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    user = crud.get_user_by_username(db=db, username=current_user.username)
    if not user:
        message = {"message": "user does not exist"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message
    template = crud.get_template(db=db, template_id=json.template_id)
    if not template:
        message = {"message": "template does not exist"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message

    goal = crud.create_goal(db=db, goal_name=json.goal_name,
                            check_in_period=json.check_in_period,
                            template_id=json.template_id,
                            user_id=user.id)

    for answer in json.responses:
        question = crud.get_question(db=db, question_id=answer.question_id)
        if not question:
            message = {"message": "question does not exist"}
            response.status_code = status.HTTP_400_BAD_REQUEST
            return message

        crud.create_response(db=db, text=answer.text, question_id=answer.question_id,
                             check_in_number=0, goal_id=goal.id)
    
    group = crud.create_group(db=db, name= json.group_name, user_id=current_user.id, template_id=goal.template_id)
    for friend in json.invites:
        friend_id = crud.get_user_by_username(db=db, username=friend).id
        crud.create_group_invite(db=db, group_id=group.group_id, user_id=friend_id)
    

    message = {"goal and group created successfully!"}
    return message

class CustomGoalNGroupInfo(BigCustomGoal):
    group_name: str
    invites: list[str]

@app.post("/create_custom_goal_and_group")
def create_custom_goal_and_group(json: CustomGoalNGroupInfo, response: Response, db: Session = Depends(get_db),
                         current_user: models.User = Depends(get_current_user)):
    # print(goaljson.questions_answers)
    if not current_user:
        message = {"message": "user not found"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message

    template = crud.create_template(db=db, name=json.goal_name, is_custom=True,
                                    creator_id=current_user.id)
    if not template:
        message = {"message": "template not created"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message

    goal = crud.create_goal(db=db, goal_name=json.goal_name, check_in_period=json.check_in_period,
                            template_id=template.template_id, user_id=current_user.id)
    if not goal:
        message = {"message": "goal not created"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message

    for QA in json.questions_answers:
        question = crud.create_question(db=db, text=QA[0], template_id=template.template_id,
                                        response_type=models.response_types(0), next_check_in_period=0)
        answer = crud.create_response(db=db, text=QA[1], question_id=question.question_id,
                                      check_in_number=0, goal_id=goal.id)
    
    group = crud.create_group(db=db, name=json.group_name, user_id=current_user.id, template_id=goal.template_id)
    for friend in json.invites:
        friend_id = crud.get_user_by_username(db=db, username=friend).id
        crud.create_group_invite(db=db, group_id=group.group_id, user_id=friend_id)

    message = {"message": "custom goal created!"}
    return message