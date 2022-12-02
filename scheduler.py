
from apscheduler.schedulers.blocking import BlockingScheduler
from email_sender import sendCheckin
from crud import update_can_check_in, delete_not_verified_users
from database import get_database
from datetime import datetime

# intialize scheduler
sched = BlockingScheduler()

# actual 
"""
Run this as soon as the day changes at 00:01 am
('cron', day_of_week='mon-sun', hour=0, minute=1)
"""
@sched.scheduled_job('cron', day_of_week='mon-sun', hour=0, minute=1)
def daily_db_update():
    # the function updates can check_in for users that have there checkin today 
    update_can_check_in(next(get_database()))
    with open("update_checkin.log", "a") as f:
        f.write(f"Actual Database update for checkin happened at: {datetime.now()} Successfully!\n")
    # function gets the user that are not verified and deletes them from the table if they are not verified after 5 days
    delete_not_verified_users(next(get_database()))
    with open("delete_users.log", "a") as f:
        f.write(f"Actual Not Verified Users Deleted at: {datetime.now()} Successfully!\n")

'''
Run this at specific time everyday 10:00 am
('cron', day_of_week='mon-sun', hour=10, minute=0)
'''
@sched.scheduled_job('cron', day_of_week='mon-sun', hour=10, minute=0)
def daily_checkin_email():   
    sendCheckin()
    with open("checkin_emails.log", "a") as f:
        f.write(f"Actual Checkin emails send at: {datetime.now()} Successfully!\n")
    

# for show
@sched.scheduled_job('interval', seconds=300)
def daily_checkin_email():  
    sendCheckin()
    with open("checkin_emails.log", "a") as f:
        f.write(f"For show Checkin emails send at: {datetime.now()} Successfully!\n")

@sched.scheduled_job('interval', seconds=300)
def daily_db_update():
    # the function updates can check_in for users that have there checkin today 
    update_can_check_in(next(get_database()))
    with open("update_checkin.log", "a") as f:
        f.write(f"For show Database update for checkin happened at: {datetime.now()} Successfully!\n")
    # function gets the user that are not verified and deletes them from the table if they are not verified after 5 days
    delete_not_verified_users(next(get_database()))
    with open("delete_users.log", "a") as f:
        f.write(f"For show Not Verified Users Deleted at: {datetime.now()} Successfully!\n")


# start the scheduler
sched.start()
