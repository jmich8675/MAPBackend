from fastapi import HTTPException
from starlette import status

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

NonexistentForumPostException = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Forum post could not be found"
)

NonexistentUserException = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="User does not exist"
)

# class NonExistent(HTTPException):
#
#     return HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail="Forum post could not be found"
#     )
