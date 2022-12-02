import json
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

# Import the SQLAlchemy parts
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import crud
from .main import app, get_db, Base2, is_running_tests
from .main import verify_access_token
from models import response_types

# Create the new database session

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def session():
    Base2.metadata.drop_all(bind=engine)
    Base2.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(session):
    # Dependency override
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    def override_is_running_tests():
        return True

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[is_running_tests] = override_is_running_tests
    yield TestClient(app)


class TestSignup:
    def test_signup_simple(self, client):
        res = client.post("/signup",
                          json={
                              "email": "user@example.com",
                              "username": "user",
                              "password": "secret"
                          })
        assert res.status_code == 200

        assert res.json()["message"] == "User created Successfully, Please verify your email"
        assert res.json()["username"] == "user"

    def test_signup_duplicate_username(self, client):
        # signup first user with username "user"
        res = client.post("/signup",
                          json={
                              "email": "user@example.com",
                              "username": "user",
                              "password": "secret"
                          })
        assert res.status_code == 200
        assert res.json()["message"] == "User created Successfully, Please verify your email"
        assert res.json()["username"] == "user"

        # signup second user with username "user"
        res = client.post("/signup",
                          json={
                              "email": "differentuser@example.com",
                              "username": "user",
                              "password": "secret"
                          })
        assert res.status_code == 400
        assert res.json()["message"] == "User with the username already exists"

    def test_signup_duplicate_email(self, client):
        # signup first user with email "user@example.com"
        res = client.post("/signup",
                          json={
                              "email": "user@example.com",
                              "username": "user",
                              "password": "secret"
                          })
        assert res.status_code == 200
        assert res.json()["message"] == "User created Successfully, Please verify your email"
        assert res.json()["username"] == "user"

        # signup second user with same email
        res = client.post("/signup",
                          json={
                              "email": "user@example.com",
                              "username": "differentuser",
                              "password": "secret"
                          })
        assert res.status_code == 400
        assert res.json()["message"] == "User with the email already exists"


@pytest.fixture()
def signup_user(client):
    user_data = {
        "email": "user@example.com",
        "username": "user",
        "password": "secret"
    }
    res = client.post("/signup", json=user_data)
    assert res.status_code == 200

    assert res.json()["message"] == "User created Successfully, Please verify your email"
    assert res.json()["username"] == "user"
    user_data["user_id"] = res.json()["user_id"]

    return user_data


@pytest.fixture()
def signup_user2(client):
    user_data = {
        "email": "user2@example.com",
        "username": "user2",
        "password": "secret2"
    }
    res = client.post("/signup", json=user_data)
    assert res.status_code == 200

    assert res.json()["message"] == "User created Successfully, Please verify your email"
    assert res.json()["username"] == "user2"
    user_data["user_id"] = res.json()["user_id"]

    return user_data


class TestLogin:
    def test_login_simple(self, client, signup_user):
        login_body = "grant_type=&username={username}&password={password}&scope=&client_id=&client_secret=".format(
            username=signup_user["username"], password=signup_user["password"])
        res = client.post("/token",
                          headers={"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                          data=login_body)
        assert res.status_code == 200
        assert res.json()["token_type"] == "bearer"
        assert verify_access_token(res.json()["access_token"], signup_user["username"])

    def test_login_incorrect_password(self, client, signup_user):
        login_body = "grant_type=&username={username}&password=incorrect_password&scope=&client_id=&client_secret=".format(
            username=signup_user["username"])
        res = client.post("/token",
                          headers={"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                          data=login_body)
        assert res.status_code == 401
        assert res.json()["detail"] == "Incorrect username or password"

    def test_login_not_registered(self, client):
        login_body = "grant_type=&username=user&password=secret&scope=&client_id=&client_secret="
        res = client.post("/token",
                          headers={"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                          data=login_body)
        assert res.status_code == 401
        assert res.json()["detail"] == "Incorrect username or password"
        assert 'access_token' not in res.json()


@pytest.fixture()
def login_user(client, signup_user):
    user_data = signup_user
    login_body = "grant_type=&username={username}&password={password}&scope=&client_id=&client_secret=".format(
        username=signup_user["username"], password=signup_user["password"])
    res = client.post("/token",
                      headers={"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                      data=login_body)
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert verify_access_token(res.json()["access_token"], signup_user["username"])
    user_data["access_token"] = res.json()["access_token"]
    return user_data


@pytest.fixture()
def login_user2(client, signup_user2):
    user_data = signup_user2
    login_body = "grant_type=&username={username}&password={password}&scope=&client_id=&client_secret=".format(
        username=signup_user2["username"], password=signup_user2["password"])
    res = client.post("/token",
                      headers={"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                      data=login_body)
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert verify_access_token(res.json()["access_token"], signup_user2["username"])
    user_data["access_token"] = res.json()["access_token"]
    return user_data


class TestForumPost:
    @pytest.mark.dependency()
    def test_create_post(self, client, login_user):
        user_data = login_user
        post = {"title": "How do I know if I'M prengan?",
                "content": "how would I know if I prengan and what are the sine's"}
        res = client.post("/create_post",
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=post)
        assert res.status_code == 201

    @pytest.mark.dependency(depends=["TestForumPost::test_create_post"])
    def test_view_post(self, client, login_user):
        user_data = login_user
        post = {"title": "How do I know if I'M prengan?",
                "content": "how would I know if I prengan and what are the sine's"}
        res = client.post("/create_post",
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=post)
        assert res.status_code == 201

        res = client.get("/see_posts?skip=0&limit=100",
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()[0]["title"] == "How do I know if I'M prengan?"
        assert res.json()[0]["content"] == "how would I know if I prengan and what are the sine's"

    @pytest.mark.dependency(depends=["TestForumPost::test_create_post"])
    def test_edit_post(self, client, login_user):
        user_data = login_user
        post = {"title": "How do I know if I'M prengan?",
                "content": "how would I know if I prengan and what are the sine's"}
        res = client.post("/create_post",
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=post)
        assert res.status_code == 201
        assert res.json()["message"] == "Post Created!"
        post_id = res.json()["post_id"]
        edited_post = {"content": "How would I know if I am pregnant and what are the signs?"}
        res = client.put("/edit_post/{post_id}".format(post_id=post_id),
                         headers={"Authorization": "Bearer " + user_data["access_token"]},
                         json=edited_post)

        res = client.get("/see_posts?skip=0&limit=100",
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()[0]["content"] == "How would I know if I am pregnant and what are the signs?"


@pytest.fixture()
def create_custom_goal(client, login_user):
    user_data = login_user
    custom_goal = {
        "goal_name": "Not Die",
        "check_in_period": 7,
        "questions_answers": [
            ["Have you eaten food recently?", "No, but I'm working on it."],
            ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
        ]
    }
    res = client.post("/create_custom_goal",
                      headers={"Authorization": "Bearer " + user_data["access_token"]},
                      json=custom_goal)
    assert res.status_code == 201
    assert res.json()["message"] == "custom goal created!"
    assert "goal_id" in res.json()
    return res.json()


class TestCustomGoal:
    @pytest.mark.dependency()
    def test_create_custom_goal(self, client, login_user):
        user_data = login_user
        custom_goal = {
            "goal_name": "Not Die",
            "check_in_period": 7,
            "questions_answers": [
                ["Have you eaten food recently?", "No, but I'm working on it."],
                ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
            ]
        }
        res = client.post("/create_custom_goal",
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=custom_goal)
        assert res.status_code == 201
        assert res.json()["message"] == "custom goal created!"
        assert "goal_id" in res.json()

    @pytest.mark.dependency(depends=["TestCustomGoal::test_create_custom_goal"])
    def test_view_custom_goal(self, client, login_user, create_custom_goal):
        user_data = login_user
        res = client.get("/goals".format(username=user_data["username"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]}, )
        assert res.status_code == 200
        assert res.json() == {'message': [{'can_check_in': False,
                                           'check_in_num': 0,
                                           'check_in_period': 7,
                                           'creator_id': 1,
                                           'goal_name': 'Not Die',
                                           'group_id': None,
                                           'id': 1,
                                           'is_achieved': False,
                                           'is_group_goal': False,
                                           'is_paused': False,
                                           'is_public': False,
                                           'next_check_in': str(date.today() + timedelta(days=7)),
                                           'start_date': str(date.today()),
                                           'template_id': 1}]}

    def test_create_custom_goal_invalid_template(self, client, login_user):
        user_data = login_user
        # test with missing goal name
        custom_goal = {
            # "goal_name": "Not Die",
            "check_in_period": 7,
            "questions_answers": [
                ["Have you eaten food recently?", "No, but I'm working on it."],
                ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
            ]
        }
        res = client.post("/create_custom_goal",
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=custom_goal)
        # 422 corresponds to invalid pydantic input
        assert res.status_code == 422

    def test_create_custom_goal_unauthorized(self, client, login_user):
        user_data = login_user
        custom_goal = {
            "goal_name": "Not Die",
            "check_in_period": 7,
            "questions_answers": [
                ["Have you eaten food recently?", "No, but I'm working on it."],
                ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
            ]
        }
        # do not pass token to test authorization
        res = client.post("/create_custom_goal".format(username=user_data["username"]),
                          # headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=custom_goal)
        assert res.status_code == 401
        assert res.json() == {"detail": "Not authenticated"}


class TestTemplate:
    @pytest.mark.dependency()
    def test_create_template(self, client, login_user):
        user_data = login_user
        template = {"name": "Template for Awesome Goal",
                    "is_custom": True}
        res = client.post("/create_template",
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=template)
        assert res.status_code == 200
        assert res.json()["message"] == "template successfully created!"

    def test_create_template_unauthorized(self, client, login_user):
        user_data = login_user
        template = {"name": "Template for Awesome Goal",
                    "is_custom": True}
        # Leave out Authorization Header
        res = client.post("/create_template".format(username=user_data["username"]),
                          # headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=template)
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"

    @pytest.mark.dependency(depends=["TestTemplate::test_create_template"])
    def test_view_template(self, client, login_user):
        # non-custom template
        user_data = login_user
        template = {"name": "Template for Awesome Goal",
                    "is_custom": False}
        res = client.post("/create_template",
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=template)
        assert res.status_code == 200
        assert res.json()["message"] == "template successfully created!"
        res = client.get("/templates",
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()[0]["name"] == "Template for Awesome Goal"


# class TestSpecificGoal:
#     def test_create_specific_goal(self, client, login_user):
#         user_data = login_user
#         # Create Template
#         template = {"name": "Template for Awesome Goal",
#                     "is_custom": True}
#         res = client.post("/{username}/create_template".format(username=user_data["username"]),
#                           headers={"Authorization": "Bearer " + user_data["access_token"]},
#                           json=template)
#         assert res.status_code == 200
#         assert res.json()["message"] == "template successfully created!"
#         # Create Specific goal
#         goal = {"goal_name": "Awesome Goal",
#                     "template_id": res.json()["template_id"],
#                 "check_in_period": 7}
#         res = client.post("/{username}/create_specific_goal".format(username=user_data["username"]),
#                           headers={"Authorization": "Bearer " + user_data["access_token"]},
#                           json=template)
#         assert res.status_code == 200


class TestCheckin:
    def test_checkin(self, session, client, login_user, create_custom_goal):
        user_data = login_user
        custom_goal_result = create_custom_goal

        res = client.get("/list_check_in_questions/{goal_id}".format(goal_id=custom_goal_result["goal_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200


class TestPauseGoal:
    @pytest.mark.dependency()
    def test_pause_goal(self, client, login_user, create_custom_goal):
        user_data = login_user
        res = client.put("/togglepause/{goal_id}".format(goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["message"] == "Pause Toggled!"
        # get goals to check if pause was successful
        res = client.get("/goals".format(username=user_data["username"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]}, )
        assert res.status_code == 200
        assert res.json()["message"][0]["is_paused"]

    @pytest.mark.dependency(depends=["TestPauseGoal::test_pause_goal"])
    def test_unpause_goal(self, client, login_user, create_custom_goal):
        user_data = login_user
        res = client.put("/togglepause/{goal_id}".format(username=user_data["username"],
                                                         goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["message"] == "Pause Toggled!"
        # Get goals to check if pause was successful
        res = client.get("/goals".format(username=user_data["username"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]}, )
        assert res.status_code == 200
        # Test if goal has been paused
        assert res.json()["message"][0]["is_paused"]
        # Send same request to unpause the goal
        res = client.put("/togglepause/{goal_id}".format(username=user_data["username"],
                                                         goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["message"] == "Pause Toggled!"
        # Get goals to check if unpause was successful
        res = client.get("/goals".format(username=user_data["username"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]}, )
        assert res.status_code == 200
        # Test if goal has been paused
        assert not res.json()["message"][0]["is_paused"]

    def test_pause_goal_unauthorized(self, client, login_user, create_custom_goal):
        user_data = login_user
        # leave out Authorization header to test if path is guarded
        res = client.put("/togglepause/{goal_id}".format(goal_id=create_custom_goal["goal_id"]))
        assert res.status_code == 401
        assert res.json() == {"detail": "Not authenticated"}


class TestAchieveGoal:
    @pytest.mark.dependency()
    def test_mark_goal_achieved(self, client, login_user, create_custom_goal):
        user_data = login_user
        res = client.put("/achieved_goal/{goal_id}".format(username=user_data["username"],
                                                           goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["message"] == "goal achieved! congrats!"
        # get goals to check if pause was successful
        res = client.get("/achieved_goals".format(username=user_data["username"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()[0]["is_achieved"]

    def test_mark_goal_achieved_invalid_goal(self, client, login_user, create_custom_goal):
        user_data = login_user
        # Use invalid goal_id
        res = client.put("/achieved_goal/{goal_id}".format(goal_id=69420),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "Goal could not be found"

    # This test is supposed to refer to a path in achieved_goal, but login methods catch it
    @pytest.mark.dependency(depends=["TestAchieveGoal::test_mark_goal_achieved"])
    def test_mark_goal_achieved_other_users_goal(self, client, login_user, login_user2, create_custom_goal):
        user_data = login_user
        user_data2 = login_user2
        # Attempt to access 'user's goal from 'user2'
        res = client.put("/achieved_goal/{goal_id}".format(goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": "Bearer " + user_data2["access_token"]})
        assert res.status_code == 403
        assert res.json()["detail"] == "Not your goal"

    def test_mark_goal_achieved_unauthorized(self, client, login_user, create_custom_goal):
        user_data = login_user
        # Leave out Authorization header
        res = client.put("/achieved_goal/{goal_id}".format(goal_id=create_custom_goal["goal_id"]))
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"


# @pytest.fixture()
# def create_question(session, create_custom_goal):
#     crud.create_question(session, "How are your goals progressing", create_custom_goal["template_id"],
#                          response_types.TYPE, 0)

@pytest.fixture()
def create_post(client, login_user):
    user_data = login_user
    post = {"title": "How do I know if I'M prengan?",
            "content": "how would I know if I prengan and what are the sine's"}
    res = client.post("/create_post",
                      headers={"Authorization": "Bearer " + user_data["access_token"]},
                      json=post)
    assert res.status_code == 201
    return res.json()


class TestComment:
    def test_leave_comment(self, client, login_user, create_post):
        user_data = login_user
        post_id = create_post["post_id"]
        # leave comment
        comment = {"text": "u prengan if pregananant"}
        res = client.post("/leave_comment/{post_id}".format(post_id=post_id),
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=comment)
        assert res.status_code == 200
        assert res.json()["message"] == "comment created!"

    def test_view_comment(self, client, login_user, create_post):
        user_data = login_user
        post_id = create_post["post_id"]
        # leave comment
        comment = {"text": "u prengan if pregananant"}
        res = client.post("/leave_comment/{post_id}".format(post_id=post_id),
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=comment)
        assert res.status_code == 200
        assert res.json()["message"] == "comment created!"

        res = client.get("/comments/{post_id}".format(post_id=post_id),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.json()[0]["content"] == "u prengan if pregananant"
        assert post_id == res.json()[0]["post_id"]

    def test_multiple_comments(self, client, login_user, create_post):
        user_data = login_user
        post_id = create_post["post_id"]
        # leave comment
        comment = {"text": "u prengan if pregananant"}
        res = client.post("/leave_comment/{post_id}".format(post_id=post_id),
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=comment)
        assert res.status_code == 200
        assert res.json()["message"] == "comment created!"
        # leave second comment
        comment2 = {"text": "i think its gg"}
        res = client.post("/leave_comment/{post_id}".format(post_id=post_id),
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=comment2)
        assert res.status_code == 200
        assert res.json()["message"] == "comment created!"
        # check to see if both appear
        res = client.get("/comments/{post_id}".format(post_id=post_id),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert len(res.json()) == 2

    def test_leave_comment_nonexistent_post(self, client, login_user):
        user_data = login_user
        comment = {"text": "u prengan if pregananant"}
        res = client.post("/leave_comment/{post_id}".format(post_id=69),
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=comment)
        assert res.status_code == 404
        assert res.json()["detail"] == "Forum post could not be found"

    def test_leave_comment_unauthorized(self, client, login_user, create_post):
        user_data = login_user
        post_id = create_post["post_id"]
        # leave comment
        comment = {"text": "u prengan if pregananant"}
        # omit Authorization header to test authentication
        res = client.post("/leave_comment/{post_id}".format(post_id=post_id),
                          # headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=comment)
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"


class TestGoalsPublicPrivate:
    def test_goal_togglepublic_private_to_public(self, client, login_user, create_custom_goal):
        user_data = login_user
        # make sure new goal is not public
        res = client.get("/public_goals/{user_id}".format(user_id=create_custom_goal["creator_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert len(res.json()) == 0
        # toggle
        res = client.put("/togglepublic/{goal_id}".format(goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.json() == "Goal now public!"
        # check if toggle worked
        res = client.get("/public_goals/{user_id}".format(user_id=create_custom_goal["creator_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.json()[0]["goal_name"] == "Not Die"
        assert res.json()[0]["is_public"]

    def test_goal_togglepublic_private_to_public_to_private(self, client, login_user, create_custom_goal):
        user_data = login_user
        # make sure new goal is not public
        res = client.get("/public_goals/{user_id}".format(user_id=create_custom_goal["creator_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert len(res.json()) == 0
        # toggle
        res = client.put("/togglepublic/{goal_id}".format(goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.json() == "Goal now public!"
        # check if toggle worked
        res = client.get("/public_goals/{user_id}".format(user_id=create_custom_goal["creator_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.json()[0]["goal_name"] == "Not Die"
        assert res.json()[0]["is_public"]
        # toggle again back to private
        res = client.put("/togglepublic/{goal_id}".format(goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.json() == "Goal now private!"

    def test_goal_togglepublic_goal_with_unassociated_user(self, client, login_user, create_custom_goal, login_user2):
        user_data = login_user
        user2_data = login_user2
        # make sure new goal is not public
        res = client.get("/public_goals/{user_id}".format(user_id=create_custom_goal["creator_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert len(res.json()) == 0
        # Attempt to get 'user' goal from 'user2'
        res = client.put("/togglepublic/{goal_id}".format(goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 403
        assert res.json()["detail"] == "Not your goal"

    def test_goal_togglepublic_unauthorized(self, client, login_user, create_custom_goal):
        user_data = login_user
        # make sure new goal is not public
        res = client.get("/public_goals/{user_id}".format(user_id=create_custom_goal["creator_id"]),
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert len(res.json()) == 0
        # Omit authorization headers to test
        res = client.put("/togglepublic/{goal_id}".format(goal_id=create_custom_goal["goal_id"]))
        # headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"


class TestSendFriendRequest:
    def test_send_friend_request(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # send friend request from user1 to user2
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.json()["detail"] == "Friend Request sent"

    def test_send_friend_request_to_nonexistent_user(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # send friend request from user1 to nonexistent user 'user69'
        res = client.post("/send_friend_request/{username}".format(username="user69"),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "User does not exist"

    def test_send_friend_request_to_self(self, client, login_user):
        user_data = login_user
        res = client.post("/send_friend_request/{username}".format(username=user_data["username"]),
                          headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 403
        assert res.json()["detail"] == "You cannot send friend requests to yourself"

    def test_send_friend_request_duplicate(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.json()["detail"] == "Friend Request sent"
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 403
        assert res.json()["detail"] == "You have already sent a friend request to that user"

    def test_send_friend_request_already_friends(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # send friend request from user1 to user2
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.json()["detail"] == "Friend Request sent"
        # accept friend request accept_friend_request
        res = client.post("/accept_friend_request/{username}".format(username=user1_data["username"]),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.json()["detail"] == "friendship accepted"
        # send friend request again
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 403
        assert res.json()["detail"] == "You are already friends with that user"

    def test_send_friend_request_unauthorized(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # send friend request from user1 to user2 unauthorized
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]))
        # headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"


class TestMyFriendRequests:
    def test_my_friend_requests(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # make sure there are no friend requests on user2's account
        res = client.get("/my_friend_requests",
                         headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert len(res.json()) == 0
        # send friend request from user1 to user2
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.json()["detail"] == "Friend Request sent"
        # check friend requests
        res = client.get("/my_friend_requests",
                         headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert len(res.json()) == 1
        assert res.json()[0] == {"username": "user", "email": "user@example.com", "id": 1}

    def test_my_friend_requests_unauthorized(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # make sure there are no friend requests on user2's account
        res = client.get("/my_friend_requests")
        # headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"


class TestAcceptFriendRequest:

    def test_accept_friend_request(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # send friend request from user1 to user2
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.json()["detail"] == "Friend Request sent"
        # accept friend request
        res = client.post("/accept_friend_request/{username}".format(username=user1_data["username"]),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.json()["detail"] == "friendship accepted"

    def test_accept_friend_request_nonexistent_user(self, client, login_user):
        user_data = login_user
        # try to accept friend request from nonexistent user with id=69
        res = client.post("/accept_friend_request/{username}".format(username="fakeUser"),
                          headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "User does not exist"

    def test_accept_friend_request_no_request_sent(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # try to accept friend request when no friend request has been sent
        res = client.post("/accept_friend_request/{username}".format(username=user1_data["username"]),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "Friend request does not exist"

    def test_accept_friend_request_already_accepted(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # send friend request from user1 to user2
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.json()["detail"] == "Friend Request sent"
        # accept friend request
        res = client.post("/accept_friend_request/{username}".format(username=user1_data["username"]),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.json()["detail"] == "friendship accepted"
        # try to accept freind request again
        res = client.post("/accept_friend_request/{username}".format(username=user1_data["username"]),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 403
        assert res.json()["detail"] == "You are already friends with that user"

    def test_accept_friend_request_unauthorized(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # send friend request from user1 to user2
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.json()["detail"] == "Friend Request sent"
        # try to accept friend request unauthorized
        res = client.post("/accept_friend_request/{username}".format(username=user1_data["username"]))
        # headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"


class TestDenyFriendRequest:
    def test_deny_friend_request(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # send friend request from user1 to user2
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.json()["detail"] == "Friend Request sent"
        res = client.post("/deny_friend_request/{username}".format(username=user1_data["username"]),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.json()["detail"] == "friendship denied successfully"

    def test_deny_friend_request_nonexistent_user(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        res = client.post("/deny_friend_request/{username}".format(username="fakeUsername"),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "User does not exist"

    def test_deny_friend_request_nonexistent_friend_request(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        res = client.post("/deny_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "Friend request does not exist"

    def test_deny_friend_request_already_friends(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # send friend request from user1 to user2
        res = client.post("/send_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.json()["detail"] == "Friend Request sent"
        # accept friend request
        res = client.post("/accept_friend_request/{username}".format(username=user1_data["username"]),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.json()["detail"] == "friendship accepted"
        res = client.post("/deny_friend_request/{username}".format(username=user2_data["username"]),
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 403
        assert res.json()["detail"] == "You are already friends with that user"


class TestChangeEmailAddress:
    def test_change_email_address(self, client, login_user):
        user_data = login_user
        body = {"email": "newEmail@example.com"}
        res = client.put("/change_email_address",
                         json=body,
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "email updated"

    def test_change_email_address_unauthorized(self, client, login_user):
        user_data = login_user
        body = {"email": "newEmail@example.com"}
        # try without auth headers
        res = client.put("/change_email_address",
                         json=body)
        # headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"


class TestChangeUsername:
    def test_change_username(self, client, login_user):
        user_data = login_user
        body = {"username": "newUsername"}
        res = client.put("/change_username",
                         json=body,
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "username updated"
        # now try to login with new username
        login_body = "grant_type=&username={username}&password={password}&scope=&client_id=&client_secret=".format(
            username=body["username"], password=user_data["password"])
        res = client.post("/token",
                          headers={"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                          data=login_body)
        assert res.status_code == 200
        assert res.json()["token_type"] == "bearer"
        assert verify_access_token(res.json()["access_token"], body["username"])

    def test_change_username_login_with_old_username(self, client, login_user):
        user_data = login_user
        body = {"username": "newUsername"}
        res = client.put("/change_username",
                         json=body,
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "username updated"
        # now try to login with new username
        login_body = "grant_type=&username={username}&password={password}&scope=&client_id=&client_secret=".format(
            username=user_data["username"], password=user_data["password"])
        res = client.post("/token",
                          headers={"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                          data=login_body)
        assert res.status_code == 401
        print(res.json())
        assert res.json()["detail"] == "Incorrect username or password"

    def test_change_username_to_existing_user(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # new username equals user2
        body = {"username": user2_data["username"]}
        res = client.put("/change_username",
                         json=body,
                         headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 403
        assert res.json()["detail"] == "That username is taken"

    def test_change_username_unauthorized(self, client, login_user):
        user_data = login_user
        body = {"username": "newUsername"}
        res = client.put("/change_username",
                         json=body)
        # headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"


class TestChangePassword:

    def test_change_password(self, client, login_user):
        user_data = login_user
        body = {"repw": user_data["password"], "newpw": "new_password"}
        res = client.put("/change_password",
                         json=body,
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "password updated"
        # now test logging in with the new password
        login_body = "grant_type=&username={username}&password={password}&scope=&client_id=&client_secret=".format(
            username=user_data["username"], password="new_password")
        res = client.post("/token",
                          headers={"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                          data=login_body)
        assert res.status_code == 200
        assert res.json()["token_type"] == "bearer"
        assert verify_access_token(res.json()["access_token"], user_data["username"])

    def test_change_password_wrong_old_password(self, client, login_user):
        user_data = login_user
        body = {"repw": "incorrect_password", "newpw": "new_password"}
        res = client.put("/change_password",
                         json=body,
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 400
        assert res.json()["detail"] == "Previous password is incorrect"
        # now test that logging in with the new password is impossible
        login_body = "grant_type=&username={username}&password={password}&scope=&client_id=&client_secret=".format(
            username=user_data["username"], password="new_password")
        res = client.post("/token",
                          headers={"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                          data=login_body)
        assert res.status_code == 401
        assert res.json()["detail"] == "Incorrect username or password"


class TestCreateSpecificGroupGoal:
    def test_create_specific_goal_and_group(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # create template
        body = {
            "name": "Template Name",
            "questions": ["Question 1?", "Question 2?"]
        }
        res = client.post("/create_template_test",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "template created successfully"
        template_id = res.json()["template_id"]
        body = {
            "goal_name": "Group Goal",
            "template_id": template_id,
            "check_in_period": 7,
            "responses": [],
            "group_name": "Epic Group",
            "invites": [
                user2_data["username"]
            ]
        }
        res = client.post("/create_specific_goal_and_group",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "goal and group created successfully!"
        # check if goal exists
        res = client.get("/goals".format(username=user1_data["username"]),
                         headers={"Authorization": "Bearer " + user1_data["access_token"]}, )
        assert res.status_code == 200
        assert res.json() == {
            'message': [
                {
                    'id': 1, 'is_paused': False, 'check_in_period': 7, 'check_in_num': 0, 'template_id': 1,
                    'can_check_in': False, 'group_id': None, 'goal_name': 'Group Goal', 'creator_id': 1,
                    'start_date': str(date.today()),
                    'next_check_in': str(date.today() + timedelta(days=7)),
                    'is_public': False, 'is_achieved': False, 'is_group_goal': False}]
        }

    def test_create_specific_goal_and_group_nonexistent_template_id(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # nonexistent template_id
        body = {
            "goal_name": "Group Goal",
            "template_id": 69,
            "check_in_period": 7,
            "responses": [],
            "group_name": "Epic Group",
            "invites": [
                user2_data["username"]
            ]
        }
        res = client.post("/create_specific_goal_and_group",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "template does not exist"
        # check if goal exists
        res = client.get("/goals".format(username=user1_data["username"]),
                         headers={"Authorization": "Bearer " + user1_data["access_token"]}, )
        assert res.status_code == 200
        assert res.json()["message"] == []

    def test_create_specific_goal_and_group_bad_question_id(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # create template
        body = {
            "name": "Template Name",
            "questions": ["Question 1?", "Question 2?"]
        }
        res = client.post("/create_template_test",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "template created successfully"
        template_id = res.json()["template_id"]
        # invalid question id
        body = {
            "goal_name": "Group Goal",
            "template_id": template_id,
            "check_in_period": 7,
            "responses": [{"text": "respond",
                           "question_id": 6}],
            "group_name": "Epic Group",
            "invites": [
                user2_data["username"]
            ]
        }
        res = client.post("/create_specific_goal_and_group",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 400
        assert res.json()["message"] == "error involving responses"

    def test_create_specific_goal_and_group_unauthorized(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # create template
        body = {
            "name": "Template Name",
            "questions": ["Question 1?", "Question 2?"]
        }
        res = client.post("/create_template_test",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "template created successfully"
        template_id = res.json()["template_id"]
        body = {
            "goal_name": "Group Goal",
            "template_id": template_id,
            "check_in_period": 7,
            "responses": [],
            "group_name": "Epic Group",
            "invites": [
                user2_data["username"]
            ]
        }
        # try without headers
        res = client.post("/create_specific_goal_and_group",
                          json=body)
        # headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"


class TestCreateCustomGroupGoal:
    def test_create_custom_goal_and_group(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        body = {
            "goal_name": "Not Die",
            "check_in_period": 7,
            "questions_answers": [
                ["Have you eaten food recently?", "No, but I'm working on it."],
                ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
            ],
            "group_name": "Epic Group",
            "invites": [
                user2_data["username"]
            ]
        }
        res = client.post("/create_custom_goal_and_group",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "custom goal and group created!"
        # check if goal exists
        res = client.get("/goals".format(username=user1_data["username"]),
                         headers={"Authorization": "Bearer " + user1_data["access_token"]}, )
        assert res.status_code == 200
        assert res.json() == {
            'message': [
                {
                    'id': 1, 'is_paused': False, 'check_in_period': 7, 'check_in_num': 0, 'template_id': 1,
                    'can_check_in': False, 'group_id': None, 'goal_name': 'Not Die', 'creator_id': 1,
                    'start_date': str(date.today()),
                    'next_check_in': str(date.today() + timedelta(days=7)),
                    'is_public': False, 'is_achieved': False, 'is_group_goal': False}]
        }

    def test_create_custom_goal_and_group_unauthorized(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        body = {
            "goal_name": "Not Die",
            "check_in_period": 7,
            "questions_answers": [
                ["Have you eaten food recently?", "No, but I'm working on it."],
                ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
            ],
            "group_name": "Epic Group",
            "invites": [
                user2_data["username"]
            ]
        }
        res = client.post("/create_custom_goal_and_group",
                          json=body)
        # headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"


class TestAcceptGroupRequest:

    def test_accept_group_request(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # user1 creates a goal and invites user2

        body = {
            "goal_name": "Not Die",
            "check_in_period": 7,
            "questions_answers": [
                ["Have you eaten food recently?", "No, but I'm working on it."],
                ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
            ],
            "group_name": "Epic Group",
            "invites": [
                user2_data["username"]
            ]
        }
        res = client.post("/create_custom_goal_and_group",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "custom goal and group created!"




        # user2 gets their goals to get the group_id
        res = client.get("/my_group_invites".format(username=user1_data["username"]),
                         headers={"Authorization": "Bearer " + user2_data["access_token"]}, )
        assert res.status_code == 200
        new_goal_group_id = res.json()[0]["group_id"]
        print("**************************")
        print(new_goal_group_id)


        res = client.post("accept_group_request/{group_id}".format(group_id=new_goal_group_id),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "group invite accepted"

        res = client.get("my_groups".format(group_id=new_goal_group_id),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})



    def test_accept_group_request_invalid_group_id(self, client, login_user):
        user_data = login_user
        # invalid group_id
        res = client.post("accept_group_request/{group_id}".format(group_id=69),
                          headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "User does not exist"

    def test_accept_group_request_not_invited(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # user1 creates a goal and invites user2

        body = {
            "goal_name": "Not Die",
            "check_in_period": 7,
            "questions_answers": [
                ["Have you eaten food recently?", "No, but I'm working on it."],
                ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
            ],
            "group_name": "Epic Group",
            "invites": [

            ]
        }
        res = client.post("/create_custom_goal_and_group",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "custom goal and group created!"

        # user2 gets their goals to get the group_id
        res = client.get("/my_group_invites".format(username=user1_data["username"]),
                         headers={"Authorization": "Bearer " + user2_data["access_token"]}, )
        assert res.status_code == 200
        assert len(res.json()) == 0


        res = client.post("accept_group_request/{group_id}".format(group_id=1),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "Friend request does not exist"

    def test_accept_group_request_twice(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # user1 creates a goal and invites user2

        body = {
            "goal_name": "Not Die",
            "check_in_period": 7,
            "questions_answers": [
                ["Have you eaten food recently?", "No, but I'm working on it."],
                ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
            ],
            "group_name": "Epic Group",
            "invites": [
                user2_data["username"]
            ]
        }
        res = client.post("/create_custom_goal_and_group",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "custom goal and group created!"

        # user2 gets their goals to get the group_id
        res = client.get("/my_group_invites".format(username=user1_data["username"]),
                         headers={"Authorization": "Bearer " + user2_data["access_token"]}, )
        assert res.status_code == 200
        new_goal_group_id = res.json()[0]["group_id"]
        print("**************************")
        print(new_goal_group_id)

        res = client.post("accept_group_request/{group_id}".format(group_id=new_goal_group_id),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "group invite accepted"

        res = client.post("accept_group_request/{group_id}".format(group_id=new_goal_group_id),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 400
        assert res.json()["detail"] == "You have already accepted that group invite"


class TestDenyGroupRequest:
    def test_deny_group_request(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # user1 creates a goal and invites user2

        body = {
            "goal_name": "Not Die",
            "check_in_period": 7,
            "questions_answers": [
                ["Have you eaten food recently?", "No, but I'm working on it."],
                ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
            ],
            "group_name": "Epic Group",
            "invites": [
                user2_data["username"]
            ]
        }
        res = client.post("/create_custom_goal_and_group",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "custom goal and group created!"

        # user2 gets their goals to get the group_id
        res = client.get("/my_group_invites".format(username=user1_data["username"]),
                         headers={"Authorization": "Bearer " + user2_data["access_token"]}, )
        assert res.status_code == 200
        new_goal_group_id = res.json()[0]["group_id"]
        print("**************************")
        print(new_goal_group_id)

        res = client.post("deny_group_request/{group_id}".format(group_id=new_goal_group_id),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "group invite denied"

        res = client.get("/my_group_invites".format(username=user1_data["username"]),
                         headers={"Authorization": "Bearer " + user2_data["access_token"]}, )
        assert res.status_code == 200
        assert len(res.json()) == 0

    def test_deny_group_request_invalid_group_id(self, client, login_user):
        user_data = login_user
        # invalid group_id
        res = client.post("deny_group_request/{group_id}".format(group_id=69),
                          headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "User does not exist"

    def test_deny_group_request_not_invited(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # user1 creates a goal and invites user2

        body = {
            "goal_name": "Not Die",
            "check_in_period": 7,
            "questions_answers": [
                ["Have you eaten food recently?", "No, but I'm working on it."],
                ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
            ],
            "group_name": "Epic Group",
            "invites": [

            ]
        }
        res = client.post("/create_custom_goal_and_group",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "custom goal and group created!"

        # user2 gets their goals to get the group_id
        res = client.get("/my_group_invites".format(username=user1_data["username"]),
                         headers={"Authorization": "Bearer " + user2_data["access_token"]}, )
        assert res.status_code == 200
        assert len(res.json()) == 0

        res = client.post("deny_group_request/{group_id}".format(group_id=1),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "Group invite does not exist"

    def test_deny_group_request_twice(self, client, login_user, login_user2):
        user1_data = login_user
        user2_data = login_user2
        # user1 creates a goal and invites user2

        body = {
            "goal_name": "Not Die",
            "check_in_period": 7,
            "questions_answers": [
                ["Have you eaten food recently?", "No, but I'm working on it."],
                ["Have you avoided getting shot?", "I haven't been shot in a month, which is great progress."]
            ],
            "group_name": "Epic Group",
            "invites": [
                user2_data["username"]
            ]
        }
        res = client.post("/create_custom_goal_and_group",
                          json=body,
                          headers={"Authorization": "Bearer " + user1_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "custom goal and group created!"

        # user2 gets their goals to get the group_id
        res = client.get("/my_group_invites".format(username=user1_data["username"]),
                         headers={"Authorization": "Bearer " + user2_data["access_token"]}, )
        assert res.status_code == 200
        new_goal_group_id = res.json()[0]["group_id"]
        print("**************************")
        print(new_goal_group_id)

        res = client.post("deny_group_request/{group_id}".format(group_id=new_goal_group_id),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["detail"] == "group invite denied"

        res = client.post("deny_group_request/{group_id}".format(group_id=new_goal_group_id),
                          headers={"Authorization": "Bearer " + user2_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["detail"] == "Group invite does not exist"


class TestMostViewActivePost:
    def test_most_active_posts(self, client, login_user):
        user_data = login_user
        post = {"title": "How do I know if I'M prengan?",
                "content": "how would I know if I prengan and what are the sine's"}
        res = client.post("/create_post",
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=post)
        assert res.status_code == 201

        res = client.get("/see_posts?skip=0&limit=100",
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()[0]["title"] == "How do I know if I'M prengan?"
        assert res.json()[0]["content"] == "how would I know if I prengan and what are the sine's"
        first_post_id = res.json()[0]["post_id"]
        print(first_post_id)
        # second post
        post = {"title": "Post 2?",
                "content": "Post content"}
        res = client.post("/create_post",
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=post)
        assert res.status_code == 201

        res = client.get("/see_posts?skip=0&limit=100",
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()[0]["title"] == "Post 2?"
        assert res.json()[0]["content"] == "Post content"

        # previous post should be second
        assert res.json()[1]["title"] == "How do I know if I'M prengan?"
        assert res.json()[1]["content"] == "how would I know if I prengan and what are the sine's"


        # leave comment
        comment = {"text": "u prengan if pregananant"}
        res = client.post("/leave_comment/{post_id}".format(post_id=first_post_id),
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=comment)
        assert res.status_code == 200
        assert res.json()["message"] == "comment created!"
        # make sure new post updated
        res = client.get("/see_posts?skip=0&limit=100",
                         headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.json()[0]["title"] == "How do I know if I'M prengan?"
        assert res.json()[0]["content"] == "how would I know if I prengan and what are the sine's"

    def test_most_active_posts_unauthorized(self, client, login_user):
        user_data = login_user
        post = {"title": "How do I know if I'M prengan?",
                "content": "how would I know if I prengan and what are the sine's"}
        res = client.post("/create_post",
                          headers={"Authorization": "Bearer " + user_data["access_token"]},
                          json=post)
        assert res.status_code == 201
        # leave out token to test unauthorized
        res = client.get("/see_posts?skip=0&limit=100")
                         #headers={"Authorization": "Bearer " + user_data["access_token"]})
        assert res.status_code == 401
        assert res.json()["detail"] == "Not authenticated"