from django.test import TestCase
import requests

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
