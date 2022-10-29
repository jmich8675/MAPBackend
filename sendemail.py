import smtplib
from dotenv import load_dotenv

from pathlib import Path
import os
 
load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)


def sendmail(subject: str = None, body: str = None, toemail: str = None):

    gmail_user = os.getenv("EMAILID")

    gmail_password = os.getenv("PASSWORD")


    sent_from = gmail_user

    to = [gmail_user]

    subject = subject

    body = 'consectetur adipiscing elit'


    email_text = """\

    From: %s

    To: %s

    Subject: %s


    %s

    """ % (sent_from, ", ".join(to), subject, body)


    try:

        smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)

        smtp_server.ehlo()

        smtp_server.login(gmail_user, gmail_password)

        smtp_server.sendmail(sent_from, to, email_text)

        smtp_server.close()

        print ("Email sent successfully!")

    except Exception as ex:

        print ("Something went wrong….",ex)


sendmail(subject="First One")
sendmail(subject="Second One")
sendmail(subject="Third One")
sendmail(subject="Fourth One")
sendmail(subject="fifth One")