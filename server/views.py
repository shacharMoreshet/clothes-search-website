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
import datetime
import pytz
import jwt
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
from jwt import decode, InvalidTokenError

# Set to store taken usernames
taken_usernames = set()

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
            "url": "https://www.shein.com/x-p-" + product["goods_id"] + "-cat-" + product["cat_id"] + ".html",
            "sold_by": "Shein"

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
            "img_url": "https://" + product["imageUrl"],
            "sold_by": "Asos"
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
        email = request_body.get('email')
        # Check if the username already exists in the set
        if username in taken_usernames:
            # Return an error response indicating that the username is already taken
            return JsonResponse({'error': 'Username already exists'})

        # Add the username to the set of taken usernames
        taken_usernames.add(username)

        # Save the sign-up data to MySQL database
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO users (username, password,email) VALUES (%s, %s, %s)", [username, password,email])

        # Return a JSON response to confirm that the sign-up was successful
        return JsonResponse({'success': True})
    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': 'Invalid request method'})

@csrf_exempt
def add_favorite_product(request):
    if request.method == 'POST':
        token = request.headers.get('Authorization')
        if not token:
            return JsonResponse({'error': 'Missing Authorization header'}, status=401)
        try:
            payload = decode(token, 'secret_key', algorithms=['HS256'])
        except InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        username = payload.get('user_id')
        request_body = json.loads(request.body)
        url = request_body.get('url')
        productName = request_body.get('name')
        productImage = request_body.get('img_url')
        productPrice = request_body.get('price')
        productOrigin = request_body.get('sold_by')

        # Save the sign-up data to MySQL database
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO favorites (username, url, productName,productImage,productPrice,productOrigin ) VALUES (%s, %s, %s, %s, %s, %s)",
                           [username, url, productName, productImage, productPrice, productOrigin])

        # Return a JSON response to confirm that the sign-up was successful
        return JsonResponse({'success': True})
    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': 'Invalid request method'})

@csrf_exempt
def get_all_favorites_products(request):
    if request.method == 'GET':
        token = request.headers.get('Authorization')
        if not token:
            return JsonResponse({'error': 'Missing Authorization header'}, status=401)
        try:
            payload = decode(token, 'secret_key', algorithms=['HS256'])
        except InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        username = payload.get('user_id')
        # Query the database for all favorite products of the user
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM favorites WHERE username=%s", [username])
            favorite_products = cursor.fetchall()
        # Create a list of favorite product objects
        favorites_list = []
        for product in favorite_products:
            product_dict = {
                'url': product[2],
                'name': product[3],
                'img_url': product[4],
                'price': product[5],
                'sold_by': product[6]
            }
            favorites_list.append(product_dict)
        # Return the list of favorite products as a JSON response
        return JsonResponse(favorites_list, safe=False)
    else:
        # Return an error response for unsupported request methods
        return JsonResponse({'error': 'Unsupported request method.'})

@csrf_exempt
def delete_favorite_product(request):
    if request.method == 'DELETE':
        token = request.headers.get('Authorization')
        if not token:
            return JsonResponse({'error': 'Missing Authorization header'}, status=401)
        try:
            payload = decode(token, 'secret_key', algorithms=['HS256'])
        except InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        username = payload.get('user_id')

        request_body = json.loads(request.body)
        product_name = request_body.get('name')
        # Delete the favorite product from the database
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM favorites WHERE username=%s AND productName=%s", [username, product_name])
        # Return a success response
        return JsonResponse({'success': 'Favorite product deleted successfully.'})
    else:
        # Return an error response for unsupported request methods
        return JsonResponse({'error': 'Unsupported request method.'})

@csrf_exempt
def add_history(request):
    if request.method == 'POST':
        token = request.headers.get('Authorization')
        if not token:
            return JsonResponse({'error': 'Missing Authorization header'}, status=401)
        try:
            payload = decode(token, 'secret_key', algorithms=['HS256'])
        except InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        username = payload.get('user_id')
        request_body = json.loads(request.body)
        url = request_body.get('url')
        tz = pytz.timezone('Israel')  # Replace with our timezone
        now = datetime.datetime.now(tz)
        current_date_time = now.strftime("%d/%m/%Y, %H:%M:%S")

        # Save the sign-up data to MySQL database
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO history (username, url, date) VALUES (%s, %s, %s)",
                [username, url, current_date_time])

        # Return a JSON response to confirm that the sign-up was successful
        return JsonResponse({'success': True})
    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': 'Invalid request method'})


def get_history(request):
    if request.method == 'GET':
        token = request.headers.get('Authorization')
        if not token:
            return JsonResponse({'error': 'Missing Authorization header'}, status=401)
        try:
            payload = decode(token, 'secret_key', algorithms=['HS256'])
        except InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        username = payload.get('user_id')
        # Query the database for all favorite products of the user
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM history WHERE username=%s", [username])
            history_products = cursor.fetchall()
        # Create a list of history objects
        history_list = []
        for product in history_products:
            product_dict = {
                'date': product[2],
                'url': product[3],
            }
            history_list.append(product_dict)
        # Return the list of favorite products as a JSON response
        return JsonResponse(history_list, safe=False)
    else:
        # Return an error response for unsupported request methods
        return JsonResponse({'error': 'Unsupported request method.'})

@csrf_exempt
def delete_history(request):
    if request.method == 'DELETE':
        token = request.headers.get('Authorization')
        if not token:
            return JsonResponse({'error': 'Missing Authorization header'}, status=401)
        try:
            payload = decode(token, 'secret_key', algorithms=['HS256'])
        except InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        username = payload.get('user_id')

        request_body = json.loads(request.body)
        url = request_body.get('url')
        date = request_body.get('date')
        # Delete the favorite product from the database
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM history WHERE username=%s AND url=%s AND date=%s", [username, url, date])
        # Return a success response
        return JsonResponse({'success': 'Product deleted successfully from history.'})
    else:
        # Return an error response for unsupported request methods
        return JsonResponse({'error': 'Unsupported request method.'})

@csrf_exempt
def edit_user_info(request):
    if request.method == 'POST':
        token = request.headers.get('Authorization')
        if not token:
            return JsonResponse({'error': 'Missing Authorization header'}, status=401)
        try:
            payload = decode(token, 'secret_key', algorithms=['HS256'])
        except InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        username = payload.get('user_id')
        request_body = json.loads(request.body)
        password = request_body.get('password')
        email = request_body.get('email')

        # Save the sign-up data to MySQL database
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password=%s, email=%s WHERE username=%s",
                [password, email, username])

        # Return a JSON response to confirm that the sign-up was successful
        return JsonResponse({'success': True})
    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': 'Invalid request method'})

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        request_body = json.loads(request.body)
        username = request_body.get('username')
        password = request_body.get('password')

        # Check if the user exists in the database
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", [username])
            user = cursor.fetchone()

        # If user exists, verify the password
        if user and (password == user[1]):
            # Generate a JWT token
            token = jwt.encode({'user_id': user[0]}, 'secret_key', algorithm='HS256')
            # Return the token as a JSON response
            return JsonResponse({'token': token})
        else:
            # Return an error response if the username, email, or password is incorrect
            return JsonResponse({'error': 'Invalid login credentials'})
    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': 'Invalid request method'})

