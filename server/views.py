from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from predict import main
import requests
import concurrent.futures
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
import json

# Define functions to make requests to SHEIN API and ASOS API
def make_shein_request(formatted_res_shein):
    url = "https://unofficial-shein.p.rapidapi.com/products/search"
    querystring = {"keywords": formatted_res_shein, "language": "en", "country": "US", "currency": "USD",
                   "sort": "0", "limit": "16", "page": "1"}
    headers = {
        "X-RapidAPI-Key": "e89d51aa0amsh2b3423580244074p1a3341jsnd51bb2cfbd9b",
        "X-RapidAPI-Host": "unofficial-shein.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    # Parse the JSON response to a Python dictionary
    response_dict = response.json()
    # Extract the fields you need from the dictionary
    info = response_dict["info"]
    origin_words = info["origin_words"]
    products = info["products"]
    extracted_products_shein = []
    for product in products:
        extracted_product = {
            "goods_id": product["goods_id"],
            "img_url": product["goods_img"],
            "name": product["goods_name"],
            "cat_id": product["cat_id"],
            "price": product["retailPrice"]["amountWithSymbol"],
            "url": "https://www.shein.com/x-p-" + product["goods_id"] + "-cat-" + product["cat_id"] + ".html"
        }
        extracted_products_shein.append(extracted_product)
    extracted_response_shein = {
        "origin_words": origin_words,
        "products_shein": extracted_products_shein
    }
    return extracted_response_shein

def model_color_to_asos_color_id(color):
    # model color options : "", "white", "black", "gray", "pink", "red", "green", "blue", "brown", "navy",
    # "beige", "yellow", "purple", "orange", "mixed color"

    # asos options: "Beige"-"25" , "Black"-"4", "Blue"-"3", "Brown"-"10", "Cream"-"20", "Gold"-"11", "Gray"-"16",
    # "Green"- "2", "Multi"-"17","Navy"-"33", "Orange"-"7", "Pink"-"9", "Purple"-"8", "Red"-"1", "Silver"-"12",
    # "Stone"-"13", "Tan"- "26", "White"-"5", "Yellow"-"6"
    if color == "white":
        return "5"
    elif color == "black":
        return "4"
    elif color == "gray":
        return "16"
    elif color == "pink":
        return "9"
    elif color == "red":
        return "1"
    elif color == "green":
        return "2"
    elif color == "blue":
        return "3"
    elif color == "brown":
        return "10"
    elif color == "navy":
        return "33"
    elif color == "beige":
        return "25"
    elif color == "yellow":
        return "6"
    elif color == "purple":
        return "8"
    elif color == "orange":
        return "7"
    elif color == "mixed color":
        return "17"
    else:
        return ""
def get_category_id(gender, item_type):
    # model types: "shirt", "jumper", "jacket", "vest", "parka", "coat", "dress"
    if gender == "man":
        if item_type == "shirt":
            return "7616"
        elif item_type == ("jacket" or "coat"):
            return "3606"
        else:
            return ""
    else:
        if item_type == "shirt":
            #return "11318"
            return "4169"
        elif item_type == ("jacket" or "coat"):
            return "2641"
        elif item_type == "dress":
            return "8799"
        else:
            return ""


def make_asos_request(color,gender, item_type):
    url = "https://asos2.p.rapidapi.com/products/v2/list"
    asos_color = model_color_to_asos_color_id(color)
    categoryId = get_category_id(gender, item_type)
    if asos_color == "":
        querystring = {"store": "US", "offset": "0", "limit": "20", "country": "US"
                       , "currency": "USD", "sizeSchema": "US", "lang": "en-US", "categoryId": categoryId}
    else:
        querystring = {"store": "US", "offset": "0", "limit": "20", "country": "US", "base_colour": asos_color
                       , "currency": "USD", "sizeSchema": "US", "lang": "en-US", "categoryId": categoryId}

    headers = {
        "X-RapidAPI-Key": "e89d51aa0amsh2b3423580244074p1a3341jsnd51bb2cfbd9b",
        "X-RapidAPI-Host": "asos2.p.rapidapi.com"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    # Parse the JSON response to a Python dictionary
    response_dict = response.json()
    # Extract the fields we need from the dictionary
    search_term = response_dict["searchTerm"]
    category_name = response_dict["categoryName"]
    products = response_dict["products"]
    extracted_products_asos = []
    for product in products:
        extracted_product = {
            "name": product["name"],
            "price": product["price"]["current"]["text"],
            "colour": product["colour"],
            "url": "https://www.asos.com/" + product["url"],
            "img_url": "https://" + product["imageUrl"]
        }
        extracted_products_asos.append(extracted_product)
    extracted_response_asos = {
        "searchTerm": search_term,
        "category_name": category_name,
        "products_asos": extracted_products_asos,
    }
    return extracted_response_asos

def get_image(request):
    image_url = request.GET.get('image_url')
    res = main(image_url)  # the response of the model
    top = res["top"]
    color = top["color"]
    gender = top["gender"]
    item_type = top["itemType"]
    formatted_res_shein = "{} {} {} {} {}".format(top["gender"], top["color"], top["itemType"], top["sleeves"],
                                            top["pattern"])

    # Make requests to SHEIN and ASOS APIs in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        shein_future = executor.submit(make_shein_request, formatted_res_shein)
        asos_future = executor.submit(make_asos_request, color, gender, item_type)

    # Extract the results from the futures
    extracted_response_shein = shein_future.result()
    extracted_response_asos = asos_future.result()
    extracted_response_asos.update(extracted_response_shein)

    # Return the combined response as JSON
    return JsonResponse(extracted_response_asos, safe=False)

@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        request_body = json.loads(request.body)
        username = request_body.get('username')
        password = request_body.get('password')

        # Save the sign-up data to MySQL database
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", [username, password])

        # Return a JSON response to confirm that the sign-up was successful
        return JsonResponse({'success': True})
    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': 'Invalid request method'})