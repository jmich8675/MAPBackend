from email.message import EmailMessage
from email.utils import formataddr
from sendemail import sendmail
from database import SessionLocal
from main import get_db
from models import User, Goal
from crud import get_goal

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
    db: Session = get_db()
    goal: Goal = get_goal(db, 2)
    print(goal)


def sendCheckin():
    sendmail(createcheckinMessage())

#sendCheckin()
queryDB()