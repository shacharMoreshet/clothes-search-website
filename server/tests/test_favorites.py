from django.test import TestCase
import requests

URL_ADD = "http://127.0.0.1:8000/favorites/add/"
HEADER = {
    "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoic2hhY2hhck0ifQ.lpMyUjZ6V_ka6OWo-frOUVDejLzfuVfHGX9jXSIR-Cg",
    "Content-Type": "application/json"
}
BODY_ADD = {
    "url": "https://www.shein.com/x-p-2903639-cat-1738.html",
    "name": "SHEIN EZwear Solid Round Neck Tee",
    "img_url": "http://img.ltwebstatic.com/images3_pi/2021/06/15/162372893685551a1c043c572a5d4aad03b6faf86e_thumbnail_405x552.jpg",
    "price": "$4.99",
    "sold_by": "Shein"
}
URL_GET = "http://127.0.0.1:8000/favorites/get/"
URL_DELETE = "http://127.0.0.1:8000/favorites/delete/"
BODY_DELETE = {"name": "SHEIN EZwear Solid Round Neck Tee"}


class FavoritesTestCase(TestCase):

    def test_add_favorite_product(self):
        response = requests.post(URL_ADD, headers=HEADER, json=BODY_ADD)  # addressing to add_favorite_product
        self.assertEqual(response.status_code, 200)
        print("\nPassed add-favorite-product test successfully")

    def test_get_all_favorite_products(self):
        response = requests.post(URL_GET, headers=HEADER, json={})  # addressing to get_all_favorites_products
        self.assertEqual(response.status_code, 200)
        print("\nPassed get-all-favorite-products test successfully")

    def test_delete_favorite_product(self):
        response = requests.post(URL_DELETE, headers=HEADER, json=BODY_DELETE)  # addressing to get_all_favorites_products
        self.assertEqual(response.status_code, 200)
        print("\nPassed delete-favorite-product test successfully")
