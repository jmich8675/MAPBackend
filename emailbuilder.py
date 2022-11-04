from email.message import EmailMessage
from email.utils import formataddr
from sendemail import sendmail
from database import get_db
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

def createMessage(emaildata: Emaildata):
    msg = EmailMessage()
    msg['Subject'] = "MAP: Reminder to Check In!" if emaildata.remainder else "MAP: It's Time to Check In!"
    msg['From'] = formataddr(("MAPS", "yoloyoyoyolo12345@gmail.com"))
    #msg['Reply-To'] = formataddr(("MAPS", "email2@domain2.example"))
    msg['To'] = formataddr(("John Smith", "yoloyoyoyolo12345@gmail.com")) #f"emaildata.email"
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
    db = next(get_db())
    goals: list[Goal] = get_checkin_goals(db)
    
    # if no goals
    if not goals:
        return None

    for goal in goals:
        user: User = get_user(db, goal.creator_id)
        #print(f"{user.username}, {user.email}")
        url = f"http://localhost:3000/email/{user.username}/{goal.id}"
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

def sendCheckin():
    email_s = generate_list_email_data()
    #print("Sendcheckin", email_s)
    # if there are checkin emails to send 
    if not email_s:
        return
        
    for email in email_s:
        sendmail(createMessage(email))

# generate_list_email_data()