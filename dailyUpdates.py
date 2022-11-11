"""
Run this as soon as the day changes
"""

from crud import update_can_check_in
from database import get_database

update_can_check_in(next(get_database()))