import jwt
from django.test import TestCase
from server.constant import HASH_ALGORITHM
from server.constant import SECRET_KEY
import requests
from django.db import connection

BODY_LOGIN = {
    "username": "Lior1",
    "password": "12345"
}
URL_LOGIN = "http://127.0.0.1:8000/login/"
URL_EDIT = "http://127.0.0.1:8000/edit/"
URL_SIGNUP = "http://127.0.0.1:8000/register/"
URL_DELETE_USER = "http://127.0.0.1:8000/delete/user/"
BODY_EDIT = {
    "password": "12345",
    "email": "Ella@gmail.com"
}
BODY_SIGNUP = {
    "username": "Or",
    "password": "123123",
    "email": "or@gmail.com"
}


class AccountTestCase(TestCase):
    def test_sign_up(self):
        header = {"Content-Type": "application/json"}
        response = requests.post(URL_SIGNUP, headers=header, json=BODY_SIGNUP)
        self.assertEqual(response.status_code, 200)
        # delete user from db
        token = jwt.encode({'user_id': "Or"}, SECRET_KEY, algorithm=HASH_ALGORITHM)
        header_delete_user = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        response_delete = requests.delete(URL_DELETE_USER, headers=header_delete_user, json={})
        self.assertEqual(response_delete.status_code, 200)
        print("\nPassed signup test successfully")

    def test_login(self):
        token = jwt.encode({'user_id': "Lior1"}, SECRET_KEY, algorithm=HASH_ALGORITHM)
        header = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        response = requests.post(URL_LOGIN, headers=header, json=BODY_LOGIN)
        self.assertEqual(response.status_code, 200)
        print("\nPassed login test successfully")

    def test_edit(self):
        token = jwt.encode({'user_id': "Ella"}, SECRET_KEY, algorithm=HASH_ALGORITHM)
        header_edit = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        response = requests.post(URL_EDIT, headers=header_edit, json=BODY_EDIT)
        self.assertEqual(response.status_code, 200)
        print("\nPassed edit test successfully")
