from emailbuilder import generate_list_email_data, createCheckinMessage, createNotificationMessage,createVerificationMessage
from sendemail import sendmail

# function to send checkin emails
def sendCheckin():
    email_s = generate_list_email_data()

    # if there are checkin emails to send 
    if not email_s:
        return
        
    for email in email_s:
        sendmail(createCheckinMessage(email))

# function to send email notification
def sendNotification(email: str, user: str, commentuser: str, comment: str, posttitle: str):
    sendmail(createNotificationMessage(email=email, user=user, commentuser=commentuser, comment=comment, posttitle=posttitle))

#function to send email Verification request
def emailVerification(email: str, user: str, token: str):
    sendmail(createVerificationMessage(email=email, user=user, token=token))

emailVerification("yoloyoyoyolo12345@gmail.com", "yolo", "Howtoimprovefitness")

    

