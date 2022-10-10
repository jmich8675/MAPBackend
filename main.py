from crypt import methods
from os import stat
from urllib.request import Request
from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from starlette.responses import RedirectResponse
import starlette.status as status
from fastapi.middleware.cors import CORSMiddleware
import bcrypt

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

#CORS STUFF
origins = [
    "https://thick-peaches-shop-73-145-245-180.loca.lt",
    "http://localhost",
    "http://localhost:8000",
    "https://localhost:8000",
    "https://localhost:3000",
    "http://localhost:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#CORS STUFF

#REQUEST MODELS
class User(BaseModel):
    email: str | None = None
    username: str
    password: str
#REQUEST MODELS

#JWT STUFF

#JWT STUFF

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
          message = {"message": "user with the email already exists"}
          response.status_code = status.HTTP_302_FOUND  
          return message
    
    # check the db to see if user with this username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        message = {"message": "user with the username already exists"}
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
    
    # TODO: generate JWT token and send it as header along with the 200 ok status

    message = {"message": "User created Successfully",
                "username": user.username }
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
    # TODO: generate JWT token and send it as header along with the 200 ok status

    message = {"message": "User Found Successfully",
                "username": user.username }
    response.status_code = status.HTTP_200_OK
    return message  

# TODO: verify JWT before accesssing this page
@app.get("/home/{username}")
def home(username: str):
    return {"home": username}