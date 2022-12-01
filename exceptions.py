from fastapi import HTTPException
from starlette import status

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

NonexistentUserException = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User does not exist"
)

NonexistentForumPostException = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Forum post could not be found"
)

ForbiddenForumPostException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not your forum post"
)

NonexistentGoalException = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Goal could not be found"
)

ForbiddenGoalException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not your goal"
)

SelfFriendRequestException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You cannot send friend requests to yourself"
)

AlreadyFriendsException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You are already friends with that user"
)

AlreadySentFriendRequestException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You have already sent a friend request to that user"
)

FriendRequestDoesNotExistException = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Friend request does not exist"
)



# class NonExistent(HTTPException):
#
#     return HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail="Forum post could not be found"
#     )
