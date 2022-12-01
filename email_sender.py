from emailbuilder import generate_list_email_data, createCheckinMessage, createNotificationMessage,createVerificationMessage, createPassResetMessage
from sendemail import sendmail

def try_and_sendmail(message):
    sent = False
    tries = 0
    while not sent:
        if tries > 5:
            break
        sent = sendmail(message)
        tries+=1
    return sent


# function to send checkin emails
def sendCheckin():
    email_s = generate_list_email_data()

    # if there are checkin emails to send 
    if not email_s:
        return
        
    for email in email_s:        
        try_and_sendmail(createCheckinMessage(email))

# function to send email notification
def sendNotification(email: str, user: str, commentuser: str, comment: str, posttitle: str):
    return try_and_sendmail(createNotificationMessage(email=email, user=user, commentuser=commentuser, comment=comment, posttitle=posttitle))

#function to send email Verification request
def emailVerification(email: str, user: str, token: str):
    return try_and_sendmail(createVerificationMessage(email=email, user=user, token=token))

#function to send pass rest links
def resetpassVerification(email: str, user: str, token: str):
    return try_and_sendmail(createPassResetMessage(email=email, user=user, token=token))

#resetpassVerification("yoloyoyoyolo12345@gmail.com", "yolo", "Howtoimprovefitness")

    

