import jwt
from django.test import TestCase
import requests
from django.db import connection

from server.constant import HASH_ALGORITHM
from server.constant import SECRET_KEY

URL_ADD = "http://127.0.0.1:8000/history/add/"
URL_GET = "http://127.0.0.1:8000/history/get/"
URL_DELETE = "http://127.0.0.1:8000/history/delete/"
HEADER = {
    "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoic2hhY2hhck0ifQ.lpMyUjZ6V_ka6OWo-frOUVDejLzfuVfHGX9jXSIR-Cg",
    "Content-Type": "application/json"
}
BODY_ADD = {"url": "http://img.ltwebstatic.com/images3_pi/2023/03/20/1679300534176ee2a0c6e503dafa7e023676397f53_thumbnail_405x552.jpg"}
BODY_DELETE = {
    "url": "https://images.asos-media.com/products/asos-design-petite-ultimate-t-shirt-with-crew-neck-in-cotton-blend-in-black-black/201329080-1-black?$n_640w$&wid=513&fit=constrain",
    "date": "22/05/2023, 15:40:01"
    }
URL_PRODUCT = "https://images.asos-media.com/products/asos-design-petite-ultimate-t-shirt-with-crew-neck-in-cotton-blend-in-black-black/201329080-1-black?$n_640w$&wid=513&fit=constrain"
USERNAME = "shacharM"
TIME = "22/05/2023, 15:40:01"
class HistoryTestCase(TestCase):

    def test_add_history(self):
        response = requests.post(URL_ADD, headers=HEADER, json=BODY_ADD)
        self.assertEqual(response.status_code, 200)
        print("\nPassed add-history test successfully")

    def test_get_history(self):
        response = requests.post(URL_GET, headers=HEADER, json={})
        self.assertEqual(response.status_code, 200)
        print("\nPassed get-history test successfully")

    def test_delete_history(self):
        token = jwt.encode({'user_id': "shacharM"}, SECRET_KEY, algorithm=HASH_ALGORITHM)
        header_delete = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        url = URL_PRODUCT
        username = USERNAME
        current_date_time = TIME
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO clothes_search.history (username, url, date) VALUES (%s, %s, %s)",
                [username, url, current_date_time])
        response = requests.post(URL_DELETE, headers=header_delete, json=BODY_DELETE)
        self.assertEqual(response.status_code, 200)
        print("\nPassed delete-history test successfully")