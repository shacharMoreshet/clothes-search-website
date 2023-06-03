from django.test import TestCase

from predict import extract_garment_attributes
from server.constant import *

class ModelTestCase(TestCase):

    def test_model(self):
        img_url = "https://img.ltwebstatic.com/images3_pi/2022/01/15/16422491726409e1fe2097a404dd1f9f055fbac5bd_thumbnail_600x.webp"
        res = extract_garment_attributes(img_url)
        top = res[TOP]
        color = top.get(COLOR, "")
        item_type = top.get(ITEM_TYPE, "")
        self.assertEqual(color, "black")
        self.assertEqual(item_type, "shirt")
        print("\nPassed model test successfully")