from email.message import EmailMessage
from email.utils import formataddr
from database import get_database
from models import User, Goal, Question, Response
from crud import get_user, get_checkin_goals, get_responses_by_goal, get_question
from datetime import date
from pydantic import BaseModel

class Emaildata(BaseModel):
    user: str
    email : str
    url : str
    questions_answers: list[list[str, str]] = []
    remainder : bool

def createCheckinMessage(emaildata: Emaildata):
    msg = EmailMessage()
    msg['Subject'] = "MAP: Reminder to Check In!" if emaildata.remainder else "MAP: It's Time to Check In!"
    msg['From'] = formataddr(("MAPS", "yoloyoyoyolo12345@gmail.com"))
    #msg['Reply-To'] = formataddr(("MAPS", "email2@domain2.example"))
    msg['To'] = formataddr((emaildata.user, emaildata.email)) #f"emaildata.email"
    body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    </head>
    <body>
    <p>Hello, {emaildata.user}</p>
    <p><a href="{emaildata.url}"> Here is the link to your goal </a></p>
    """
    if emaildata.questions_answers:
        body += """
            <p>Summary for last time</p>
            <table>
            <tr>
            <th>Question</th>
            <th>Answer</th>
            <tr>
            """
        for qa in emaildata.questions_answers:
            body += f"""
            <tr>
            <td>{qa[0]}</td>
            <td>{qa[1]}</td>
            </tr>
            """
        body += """
        </table>
        """
    body += """
    <p>Regards, </p>
    <p>Team MAP</p>
    </body>
    </html>
    """    
    msg.set_content(body, subtype='html')

    return msg   

def generate_list_email_data():
    emaildata_s : list(Emaildata) = list()
    #print(emaildata_s)
    db = next(get_database())
    goals: list[Goal] = get_checkin_goals(db)
    
    # if no goals
    if not goals:
        return None

    for goal in goals:
        user: User = get_user(db, goal.creator_id)
        #print(f"{user.username}, {user.email}")
        #url = f"http://localhost:3000/email/{user.username}/{goal.id}"
        url = "http://localhost:3000/login"
        responses: list[Response] = get_responses_by_goal(db, goal.id)
        # filter responses to only have responses with previous check_in_num
        responses = [response for response in responses if response.check_in_number == goal.check_in_num]

        #print(url)
        # get responses and associated questions
        qa_s = list()
        for response in responses:
            question: Question = get_question(db, response.goal_id)
            qa = [question.text, response.text]
            qa_s.append(qa)

        #print(qa_s)
        remainder = False if goal.next_check_in == date.today() else True

        data = Emaildata(user = user.username,email = user.email, url = url, questions_answers= qa_s, remainder=remainder)
        emaildata_s.append(data)
    return emaildata_s 

def createNotificationMessage(email: str, user: str, commentuser: str, comment: str, posttitle: str):
    msg = EmailMessage()
    msg['Subject'] = "Notification Alert from MAPS"
    msg['From'] = formataddr(("MAPS", "yoloyoyoyolo12345@gmail.com"))
    #msg['Reply-To'] = formataddr(("MAPS", "email2@domain2.example"))
    msg['To'] = formataddr((user, email))
    body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    </head>
    <body>
    <p>Hi, {user}</p>
    
    <p>{commentuser} has commented "{comment}" on your post titled "{posttitle}"</p>

    <p>Regards, </p>
    <p>Team MAPS</p>
    </body>
    </html>
    """

    msg.set_content(body, subtype='html')

    return msg

def createVerificationMessage(email: str, user: str, token: str):
    url = f"http://localhost:3000/verify_email/{token}"
    msg = EmailMessage()
    msg['Subject'] = "MAP: Email Verification"
    msg['From'] = formataddr(("MAPS", "yoloyoyoyolo12345@gmail.com"))
    msg['To'] = formataddr((user, email))
    body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    </head>
    <body>
    <p>Hello, {user}</p>
    <p><a href="{url}"> Click the link to verify your email </a></p>
    <p>Regards, </p>
    <p>Team MAP</p>
    </body>
    </html>
    """    
    msg.set_content(body, subtype='html')

    return msg   
