import json
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

# Import the SQLAlchemy parts
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import crud
from .main import app, get_db, Base2
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

    app.dependency_overrides[get_db] = override_get_db
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

        assert res.json()["message"] == "User created Successfully"
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
        assert res.json()["message"] == "User created Successfully"
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
        assert res.json()["message"] == "User created Successfully"
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

    assert res.json()["message"] == "User created Successfully"
    assert res.json()["username"] == "user"

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

    assert res.json()["message"] == "User created Successfully"
    assert res.json()["username"] == "user2"

    return user_data


class TestLogin:
    def test_login_simple(self, client, signup_user):
        res = client.post("/login", json=signup_user)
        assert res.status_code == 200
        assert res.json()["message"] == "User logged in successfully"
        assert res.json()["username"] == "user"
        assert verify_access_token(res.json()["access_token"], signup_user["username"])

    def test_login_incorrect_password(self, client, signup_user):
        incorrect_user_data = {"username": signup_user["username"], "password": "incorrectPassword"}
        res = client.post("/login", json=incorrect_user_data)
        assert res.status_code == 403
        assert res.json()["message"] == "Incorrect Password"
        assert 'access_token' not in res.json()

    def test_login_not_registered(self, client):
        user_data = {
            "username": "user",
            "password": "secret"
        }
        res = client.post("/login", json=user_data)
        assert res.status_code == 403
        assert res.json()["message"] == "user with the username does not exist"
        assert 'access_token' not in res.json()


@pytest.fixture()
def login_user(client, signup_user):
    user_data = signup_user
    res = client.post("/login", json=user_data)
    assert res.status_code == 200
    assert res.json()["message"] == "User logged in successfully"
    assert res.json()["username"] == "user"
    assert verify_access_token(res.json()["access_token"], signup_user["username"])
    user_data["access_token"] = res.json()["access_token"]
    return user_data


@pytest.fixture()
def login_user2(client, signup_user2):
    user_data = signup_user2
    res = client.post("/login", json=user_data)
    assert res.status_code == 200
    assert res.json()["message"] == "User logged in successfully"
    assert res.json()["username"] == "user2"
    assert verify_access_token(res.json()["access_token"], user_data["username"])
    user_data["access_token"] = res.json()["access_token"]
    return user_data


class TestForumPost:
    @pytest.mark.dependency()
    def test_create_post(self, client, login_user):
        user_data = login_user
        post = {"title": "How do I know if I'M prengan?",
                "content": "how would I know if I prengan and what are the sine's"}
        res = client.post("/{username}/create_post".format(username=user_data["username"]),
                          headers={"Authorization": user_data["access_token"]},
                          json=post)
        assert res.status_code == 201

    # NEED PULL
    @pytest.mark.dependency(depends=["TestForumPost::test_create_post"])
    def test_view_post(self, client, login_user):
        user_data = login_user
        post = {"title": "How do I know if I'M prengan?",
                "content": "how would I know if I prengan and what are the sine's"}
        res = client.post("/{username}/create_post".format(username=user_data["username"]),
                          headers={"Authorization": user_data["access_token"]},
                          json=post)
        assert res.status_code == 201


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
    res = client.post("/{username}/create_custom_goal".format(username=user_data["username"]),
                      headers={"Authorization": user_data["access_token"]},
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
        res = client.post("/{username}/create_custom_goal".format(username=user_data["username"]),
                          headers={"Authorization": user_data["access_token"]},
                          json=custom_goal)
        assert res.status_code == 201
        assert res.json()["message"] == "custom goal created!"
        assert "goal_id" in res.json()

    @pytest.mark.dependency(depends=["TestCustomGoal::test_create_custom_goal"])
    def test_view_custom_goal(self, client, login_user, create_custom_goal):
        user_data = login_user
        res = client.get("/{username}".format(username=user_data["username"]),
                         headers={"Authorization": user_data["access_token"]}, )
        assert res.status_code == 200
        assert res.json() == {'message': [
            {'id': 1, 'is_paused': False, 'check_in_period': 7, 'check_in_num': 0, 'template_id': 1,
             'can_check_in': False, 'creator_id': 1, 'goal_name': 'Not Die', 'start_date': str(date.today()),
             'next_check_in': str(date.today() + timedelta(days=7)), 'is_public': False, 'is_achieved': False}]}

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
        res = client.post("/{username}/create_custom_goal".format(username=user_data["username"]),
                          headers={"Authorization": user_data["access_token"]},
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
        res = client.post("/anotherUser/create_custom_goal".format(username=user_data["username"]),
                          # headers={"Authorization": user_data["access_token"]},
                          json=custom_goal)
        assert res.status_code == 401
        assert res.json() == {"message": "User Not logged in"}


class TestCheckin:
    def test_checkin(self, session, client, login_user, create_custom_goal):
        user_data = login_user
        custom_goal_result = create_custom_goal

        res = client.get("/{username}/{goal_id}/list_check_in_questions".format(username=user_data["username"],
                                                                                goal_id=custom_goal_result["goal_id"]),
                         headers={"Authorization": user_data["access_token"]})
        assert res.status_code == 200
        print(res.json())


class TestPauseGoal:
    @pytest.mark.dependency()
    def test_pause_goal(self, client, login_user, create_custom_goal):
        user_data = login_user
        res = client.put("/{username}/{goal_id}/togglepause".format(username=user_data["username"],
                                                                    goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["message"] == "Pause Toggled!"
        # get goals to check if pause was successful
        res = client.get("/{username}".format(username=user_data["username"]),
                         headers={"Authorization": user_data["access_token"]}, )
        assert res.status_code == 200
        assert res.json()["message"][0]["is_paused"]

    @pytest.mark.dependency(depends=["TestPauseGoal::test_pause_goal"])
    def test_unpause_goal(self, client, login_user, create_custom_goal):
        user_data = login_user
        res = client.put("/{username}/{goal_id}/togglepause".format(username=user_data["username"],
                                                                    goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["message"] == "Pause Toggled!"
        # Get goals to check if pause was successful
        res = client.get("/{username}".format(username=user_data["username"]),
                         headers={"Authorization": user_data["access_token"]}, )
        assert res.status_code == 200
        # Test if goal has been paused
        assert res.json()["message"][0]["is_paused"]
        # Send same request to unpause the goal
        res = client.put("/{username}/{goal_id}/togglepause".format(username=user_data["username"],
                                                                    goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["message"] == "Pause Toggled!"
        # Get goals to check if unpause was successful
        res = client.get("/{username}".format(username=user_data["username"]),
                         headers={"Authorization": user_data["access_token"]}, )
        assert res.status_code == 200
        # Test if goal has been paused
        assert not res.json()["message"][0]["is_paused"]

    def test_pause_goal_unauthorized(self, client, login_user, create_custom_goal):
        user_data = login_user
        # leave out Authorization header to test if path is guarded
        res = client.put("/{username}/{goal_id}/togglepause".format(username=user_data["username"],
                                                                    goal_id=create_custom_goal["goal_id"]))
        assert res.status_code == 401
        assert res.json() == {"message": "User Not logged in"}


class TestAchieveGoal:
    @pytest.mark.dependency()
    def test_mark_goal_achieved(self, client, login_user, create_custom_goal):
        user_data = login_user
        res = client.put("/{username}/{goal_id}/achieved_goal".format(username=user_data["username"],
                                                                      goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()["message"] == "goal achieved! congrats!"
        # get goals to check if pause was successful
        res = client.get("/{username}/achieved_goals".format(username=user_data["username"]),
                         headers={"Authorization": user_data["access_token"]})
        assert res.status_code == 200
        assert res.json()[0]["is_achieved"]

    def test_mark_goal_achieved_invalid_goal(self, client, login_user, create_custom_goal):
        user_data = login_user
        # Use invalid goal_id
        res = client.put("/{username}/{goal_id}/achieved_goal".format(username=user_data["username"],
                                                                      goal_id=69420),
                         headers={"Authorization": user_data["access_token"]})
        assert res.status_code == 404
        assert res.json()["message"] == "error: goal not found"

    # This test is supposed to refer to a path in achieved_goal, but login methods catch it
    @pytest.mark.dependency(depends=["TestAchieveGoal::test_mark_goal_achieved"])
    def test_mark_goal_achieved_other_users_goal(self, client, login_user, login_user2, create_custom_goal):
        user_data = login_user
        user_data2 = login_user2
        # Attempt to access 'user's goal from 'user2'
        res = client.put("/{username}/{goal_id}/achieved_goal".format(username=user_data["username"],
                                                                      goal_id=create_custom_goal["goal_id"]),
                         headers={"Authorization": user_data2["access_token"]})
        assert res.status_code == 401
        assert res.json()["message"] == "User Not logged in"

    def test_mark_goal_achieved_unauthorized(self, client, login_user, create_custom_goal):
        user_data = login_user
        # Leave out Authorization header
        res = client.put("/{username}/{goal_id}/achieved_goal".format(username=user_data["username"],
                                                                      goal_id=create_custom_goal["goal_id"]))
        assert res.status_code == 401
        assert res.json()["message"] == "User Not logged in"

# @pytest.fixture()
# def create_question(session, create_custom_goal):
#     crud.create_question(session, "How are your goals progressing", create_custom_goal["template_id"],
#                          response_types.TYPE, 0)
