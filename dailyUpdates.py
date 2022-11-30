"""
Run this as soon as the day changes
"""

from crud import update_can_check_in, delete_not_verified_users
from database import get_database

# the function updates can check_in for users that have there checkin today
update_can_check_in(next(get_database()))

# function gets the user that are not verified and deletes them from the table if they are not verified after 5 days
delete_not_verified_users(next(get_database()))

