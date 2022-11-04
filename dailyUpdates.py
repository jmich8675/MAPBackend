"""
Run this as soon as the day changes
"""

from crud import update_can_check_in
from database import get_db

update_can_check_in(next(get_db()))