from email.message import EmailMessage
from email.utils import formataddr
from sendemail import sendmail
import database
from models import User, Goal
from crud import get_goal
from fastapi import Depends

# #DATABASE
from sqlalchemy.orm import Session
# from database import SessionLocal, engine

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
# #DATABASE


def createcheckinMessage():
    msg = EmailMessage()
    msg['Subject'] = "CHECK-IN ALERT"
    msg['From'] = formataddr(("MAPS", "yoloyoyoyolo12345@gmail.com"))
    #msg['Reply-To'] = formataddr(("MAPS", "email2@domain2.example"))
    msg['To'] = formataddr(("John Smith", "yoloyoyoyolo12345@gmail.com"))
    msg.set_content("""\
    <html>
    <head></head>
    <body>
        <p>A simple test email</p>
    </body>
    </html>
    """, subtype='html')

    return msg

def createRemainderMessage():
    pass

def queryDB():
    goal: Goal = get_goal(next(database.get_db()), 1)
    print(goal.goal_name)

def sendCheckin():
    sendmail(createcheckinMessage())

#sendCheckin()
queryDB()