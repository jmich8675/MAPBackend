from functools import wraps
from time import perf_counter
import re

# Make a regular expression
# for validating an Email

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

def measure_time(func):
    """decorator to measure time for function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):

        start_time = perf_counter()

        result = func(*args, **kwargs)

        delta = round(perf_counter() - start_time, 5)

        print(f"\033[48;5;4m{func.__name__} : {delta*1000} ms\033[0m")

        return result

    return wrapper

def is_email(email : str): 
    # pass the regular expression
    # and the string into the fullmatch() method
    if(re.fullmatch(regex, email)):
        return True
 
    else:
        return False
