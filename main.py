from email import header
import re
from urllib import request
from fastapi import FastAPI, Response, status, Request
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
from fastapi.exceptions import RequestValidationError

#DATABASE
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
#DATABASE

app = FastAPI()

#REQUEST MODELS
class User(BaseModel):
    email: str | None = None
    username: str
    password: str
#REQUEST MODELS

#JWT STUFF
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

def verify_access_token(token: str, username: str):
    print("verify function")
    try:
        print("inside try")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username_payload: str = payload.get("sub")
        if username_payload is None:
            return False
        if username_payload != username:
            return False
    except JWTError:
        return False
    return True


class IsLoggedIn(APIRoute):
    def get_route_handler(self) -> callable:
        original_route_handler = super().get_route_handler()

        async def route_authentication_handler(request: Request) -> Response:
            # credentials_exception = HTTPException(
            #     status_code=status.HTTP_401_UNAUTHORIZED,
            #     detail="Could not validate credentials",
            #     headers={"WWW-Authenticate": "Bearer"},
            # )
            urls = ["/login", "/signup", "/", "/docs", "/openapi.json", "/redoc", "/update_database"]
            print(request.url.path)
            if (request.url.path not in urls):
                token = request.headers.get('Authorization', None)
                username = request.url.path.split('/')[1]

                if (not token) or (not verify_access_token(token, username)):
                    return JSONResponse(content={
                            "message": "User Not logged in"
                        }, status_code=status.HTTP_400_BAD_REQUEST)
            try:
                return await original_route_handler(request)
            except RequestValidationError as exc:
                    body = await request.body()
                    detail = {"errors": exc.errors(), "body": body.decode()}
                    raise HTTPException(status_code=422, detail=detail)
        return route_authentication_handler
#JWT STUFF
#CORS STUFF
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
app.router.route_class = IsLoggedIn
#CORS STUFF

@app.get("/")
def root():
    return {"message": "Welcome to MAP website"}

# trying post request
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

    #generate a salt
    salt = bcrypt.gensalt(12)    
    #combine and generate the pass hash
    passhash = bcrypt.hashpw(user.password.encode('utf-8'), salt)
    salt = salt.decode('utf-8')
    passhash = passhash.decode('utf-8')
    print(f"{salt} {passhash}")

    #make a schema
    new_user = schemas.UserCreate(email=user.email, username=user.username,
                          pw_hash=passhash, pw_salt=salt)
    new_user = crud.create_user(db, new_user)

    # if not successful database transaction
    if not new_user:
        message = {"message": "Error Occured while creating the user"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message
    
    # generate JWT token and send it as header along with the 200 ok status
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    message = {"message": "User created Successfully",
                "username": user.username,
                "access_token": access_token, 
                "token_type": "Bearer"}
    response.status_code = status.HTTP_200_OK
    return message

@app.post("/login")
def login(user: User, response: Response, db: Session = Depends(get_db)):
    print(f"login {user.username} {user.password}")

    # check the db to see if user with this username does not exist
    db_user = crud.get_user_by_username(db, username=user.username)
    if not db_user:
        message = {"message": "user with the username does not exist"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message

    # IS A RETURNING USER

    # see if the given password match with the password in db    
    db_passhash = bytes(db_user.pw_hash, 'utf-8')
    salt = bytes(db_user.pw_salt, 'utf-8')
    curr_passhash = bcrypt.hashpw(user.password.encode('utf-8'), salt)

    print(f"{salt} {db_passhash} {curr_passhash}")
    #verify password
    if db_passhash != curr_passhash:
        message = {"message": "Incorrect Password"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message
    
    #is the correct user
    # generate JWT token and send it as header along with the 200 ok status
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    message = {"message": "User logged in successfully",
                "username": user.username,
                "access_token": access_token, 
                "token_type": "bearer"}
    response.status_code = status.HTTP_200_OK
    return message  


@app.get("/{username}")
def home(username: str, db: Session=Depends(get_db)):
    return {"message": crud.get_user_goals(db=db, username=username)}

class SmallResponse(BaseModel):
    text: str
    question_id: int

class BigGoal(BaseModel):
    goal_name: str
    template_id: int
    check_in_period: int
    responses: list[SmallResponse] = []


@app.post("/{username}/create_specific_goal")
def create_specific_goal(goaljson: BigGoal, username: str, response: Response, db: Session=Depends(get_db)):
    user = crud.get_user_by_username(db=db, username=username)
    if not user:
        message={"message": "user does not exist"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message
    template = crud.get_template(db=db, template_id=goaljson.template_id)
    if not template:
        message={"message": "template does not exist"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message
    
    goal = crud.create_goal(db=db, goal_name=goaljson.goal_name, 
                              check_in_period=goaljson.check_in_period,
                              template_id=goaljson.template_id,
                              user_id=user.id)

    for answer in goaljson.responses:
        question = crud.get_question(db=db, question_id=answer.question_id)
        if not question:
            message={"message": "question does not exist"}
            response.status_code = status.HTTP_400_BAD_REQUEST
            return message
        
        crud.create_response(db=db, text=answer.text, question_id=answer.question_id,
                             check_in_number=0, goal_id = goal.id)
    message={"goal and responses created successfully!"}
    response.status_code = status.HTTP_201_CREATED
    return message
    

class BigCustomGoal(BaseModel):
    goal_name: str
    check_in_period: int
    questions_answers: list[list[str, str]] = []
        
@app.post("/{username}/create_custom_goal")
def create_custom_goal(goaljson: BigCustomGoal, username: str, 
                       response: Response, db: Session=Depends(get_db)):
    user = crud.get_user_by_username(db=db, username=username)
    if not user:
        message={"message": "user not found"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        return message
    
    template = crud.create_template(db=db, name=goaljson.goal_name,is_custom=True,
                                     creator_id=user.id)
    if not template:
        message={"message": "template not created"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message
    
    goal = crud.create_goal(db=db, goal_name=goaljson.goal_name, check_in_period=goaljson.check_in_period,
                             template_id=template.template_id, user_id=user.id)
    if not goal:
        message={"message": "goal not created"}
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return message
    
    for QA in goaljson.questions_answers:
        question = crud.create_question(db=db, text=QA[0], template_id=template.template_id,
                                        response_type=models.response_types(0), next_check_in_period=0)
        answer = crud.create_response(db=db, text=QA[1], question_id=question.question_id,
                                      check_in_number=0, goal_id=goal.id)
    
    message={"custom goal created!"}
    response.status_code = status.HTTP_201_CREATED
    return message

@app.post("/{username}/create_template")
def create_template(username: str, template: schemas.TemplateCreate,
                    response: Response, db: Session=Depends(get_db)):
    user = crud.get_user_by_username(db=db, username=username)
    if not user:
        message = {"message": "error: user not found"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message
    creator_id = user.id
    crud.create_template(db=db, name=template.name, is_custom=template.is_custom, 
                         creator_id=creator_id)
    message = {"message": "template successfully created!"}
    return message

class GoalInfo(BaseModel):
    name: str
    start_date: date
    check_in_period: int
    next_check_in: date

@app.get("/{username}/{goal_id}/progress")
def view_goal_progress(username: str, goal_id: int, response: Response, db: Session=Depends(get_db)):
    user = crud.get_user_by_username(db=db, username=username)
    goal = crud.get_goal(db=db, goal_id=goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_404_NOT_FOUND
        return message
    if goal.creator_id != user.id:
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

@app.get("/{username}/templates", response_model=list[schemas.Template])
def view_premade_templates(db: Session=Depends(get_db), skip: int = 0, limit: int = 100):
    return crud.get_premade_templates(db=db, skip=skip, limit=limit)

class PastWriting(BaseModel):
    question: str
    answer: str
    check_in_number: int

@app.get("/{username}/{goal_id}/responses")
def view_responses(goal_id: int, response: Response, db: Session=Depends(get_db)):
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
 
@app.post("/{username}/create_response")
def create_response(resp: schemas.ResponseCreate, response: Response,
                    db: Session=Depends(get_db)):
    goal = crud.get_goal(db=db, goal_id=resp.goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_403_FORBIDDEN
        return message
    crud.create_response(db=db, response=resp)
    message = {"message": "response created!"}
    return message

@app.put("/{username}/{goal_id}/achieved_goal")
def achieved_goal(username: str, goal_id: int, response: Response, db: Session=Depends(get_db)):
    user = crud.get_user_by_username(db=db, username=username)
    goal = crud.get_goal(db=db, goal_id=goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_404_NOT_FOUND
        return message
    if goal.creator_id != user.id:
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

@app.delete("/{username}/{goal_id}/delete_goal")
def delete_goal(username: str, goal_id: int, response: Response, db: Session=Depends(get_db)):
    user = crud.get_user_by_username(db=db, username=username)
    goal = crud.get_goal(db=db, goal_id=goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_404_NOT_FOUND
        return message
    if goal.creator_id != user.id:
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

@app.put("/{username}/{goal_id}/edit_check_in_period")
def edit_check_in_period(username: str, goal_id: int, check_in_period: CheckInPeriod,
                         response: Response, db: Session=Depends(get_db)):
    user = crud.get_user_by_username(db=db, username=username)
    goal = crud.get_goal(db=db, goal_id=goal_id)
    if not goal:
        message = {"message": "error: goal not found"}
        response.status_code = status.HTTP_404_NOT_FOUND
        return message
    if goal.creator_id != user.id:
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
def update_database(response: Response, db: Session=Depends(get_db)):
    crud.update_can_check_in(db=db)
    message = {"message": "database updated"}
    response.status_code = status.HTTP_200_OK
    return message

@app.get("/{username}/{goal_id}/list_check_in_quetsions")
def list_check_in_questions(username: str, goal_id: int, db: Session=Depends(get_db)):
    #error checking
    user = crud.get_user_by_username(db=db, username=username)
    goal = crud.get_goal(db=db, goal_id=goal_id)
    return crud.get_check_in_questions(db=db, this_check_in=goal.check_in_num + 1, this_template=goal.template_id)

class CheckInAnswers(BaseModel):
    answers: list[schemas.ResponseBase] = []

@app.post("/{username}/{goal_id}/check_in")
def check_in(username: str, goal_id: int, check_in_answers: CheckInAnswers,
             response: Response, db: Session=Depends(get_db)):
    
    goal = crud.get_goal(db=db, goal_id=goal_id)
    for answer in check_in_answers.answers:
        question = crud.get_question(db=db, question_id=answer.question_id)
        if not question:
            message={"message": "question does not exist"}
            response.status_code = status.HTTP_400_BAD_REQUEST
            return message
        
        crud.create_response(db=db, text=answer.text, question_id=answer.question_id,
                             check_in_number=0, goal_id=goal.id)
    message={"answers created successfully!"}
    response.status_code = status.HTTP_201_CREATED
    return message