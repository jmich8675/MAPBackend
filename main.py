from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import RedirectResponse
import starlette.status as status

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

dummyDB = {}

@app.get("/")
async def root():
    return {"message": "Welcome to MAP website"}

# trying path parameters 

@app.get("/users/{user_id}")
async def read_user(user_id: int | None = None):
    # database query with user_id
    dummy = {"username" : "Ayush"}
    return {"user_id": user_id, "dummydata": dummy}


# trying query parameters : things after ? in the url string

@app.get("/goals/")
async def read_item(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

class User(BaseModel):
    name: str
    password: str
#this user is outdated. our class declarations exists in schemas.py

# trying post request
@app.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    print(f"signup {user.username} {user.pw_hash}")
    # check the dummy database if user exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
          print("email already registered") #will probably raise httpexception here
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
          print("username already exists")
    #if checkpassword != None:
        # take the already present user to login page
        #return RedirectResponse(url=app.url_path_for("login"))
    crud.create_user(db=db, user=user)
    return RedirectResponse(f'/home/{user.username}', status_code=status.HTTP_302_FOUND)

@app.post("/login")
def login(user: User):
    print(f"login {user.name} {user.password}")
    # check the dummy database if user exists
    checkpassword = dummyDB.get(user.name)
    
    if checkpassword == None:
        # take not present user to signup page
        return RedirectResponse(url=app.url_path_for("signup"))

    if checkpassword != user.password:
        return {"message" : "wrong password"}

    return RedirectResponse(f'/home/{user.name}', status_code=status.HTTP_302_FOUND)

@app.get("/home/{username}")
def home(username: str):
    return {"home": username}
