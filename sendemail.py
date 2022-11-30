import smtplib
from dotenv import load_dotenv

from pathlib import Path
import os
 
load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)


def sendmail(message):
    gmail_user = os.getenv("EMAILID")
    gmail_password = os.getenv("PASSWORD")

    try:

        smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_server.ehlo()
        smtp_server.login(gmail_user, gmail_password)
        #smtp_server.sendmail(sent_from, to, email_text)
        smtp_server.send_message(message)
        smtp_server.close()
        print ("Email sent successfully!")
        return True
        
    except Exception as ex:
        print ("Something went wrong….",ex)
        return False