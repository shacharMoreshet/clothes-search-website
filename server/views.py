from .constant import *
from predict import extract_garment_attributes
import requests
import concurrent.futures
import json
import datetime
import pytz
import jwt
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from jwt import decode, InvalidTokenError


# Set to store taken usernames
taken_usernames = set()

# Define functions to make requests to SHEIN API and ASOS API
def make_shein_request(formatted_res_shein):
    url = SHEIN_URL_API
    querystring = {"keywords": formatted_res_shein, "language": LANGUAGE, "country": COUNTRY,
                   "currency": CURRENCY, "sort": SORT, "limit": LIMIT, "page": PAGE}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST_SHEIN
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
    return COLOR_MAPPING.get(color, "")

def get_category_id(gender, item_type):
    if gender in CATEGORY_MAPPING and item_type in CATEGORY_MAPPING[gender]:
        return CATEGORY_MAPPING[gender][item_type]
    elif item_type in CATEGORY_MAPPING["woman"]:
        return CATEGORY_MAPPING["woman"][item_type]
    return ""

def make_asos_request(color, gender, item_type):
    url = ASOS_URL_API
    asos_color = model_color_to_asos_color_id(color)
    categoryId = get_category_id(gender, item_type)
    if asos_color == "":
        querystring = {"store": STORE, "offset": OFFSET, "limit": LIMIT, "country": COUNTRY
            , "currency": CURRENCY, "sizeSchema": SIZESCHEMA, "lang": LANGUAGE_ASOS, "categoryId": categoryId}
    else:
        querystring = {"store": STORE, "offset": OFFSET, "limit": LIMIT,
                       "country": COUNTRY, "base_colour": asos_color , "currency": CURRENCY,
                       "sizeSchema": SIZESCHEMA, "lang": LANGUAGE_ASOS, "categoryId": categoryId}

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST_ASOS
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
    image_url = request.GET.get(IMG_URL)
    res = extract_garment_attributes(image_url)  # the response of the model
    top = res[TOP]
    color = top.get(COLOR, "")
    gender = top.get(GENDER, "")
    item_type = top.get(ITEM_TYPE, "")
    sleeves = top.get(SLEEVES, "")
    pattern = top.get(PATTERN, "")
    if color == "" and gender == "" and item_type == "":
        response_data = {'error': ERROR_MODEL}
        return JsonResponse(response_data, status=400)
    formatted_res_shein = "{} {} {} {} {}".format(gender, color, item_type, sleeves,
                                                  pattern)
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
        username = request_body.get(USERNAME)
        password = request_body.get(PASSWORD)
        email = request_body.get(EMAIL)
        # Check if the username already exists in the set
        if username in taken_usernames:
            # Return an error response indicating that the username is already taken
            return JsonResponse({'error': ERROR_USERNAME_EXISTS})

        # Add the username to the set of taken usernames
        taken_usernames.add(username)

        # Save the sign-up data to MySQL database
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO users (username, password,email) VALUES (%s, %s, %s)",
                           [username, password, email])

        # Return a JSON response to confirm that the sign-up was successful
        return JsonResponse({'success': True})
    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': ERROR_REQUEST_METHOD})


@csrf_exempt
def add_favorite_product(request):
    if request.method == 'POST':
        token = request.headers.get(AUTHORIZATION)
        if not token:
            return JsonResponse({'error': ERROR_MISSING_TOKEN}, status=401)
        try:
            payload = decode(token, SECRET_KEY, algorithms=[HASH_ALGORITHM])
        except InvalidTokenError:
            return JsonResponse({'error': ERROR_INVALID_TOKEN}, status=401)
        username = payload.get('user_id')
        request_body = json.loads(request.body)
        url = request_body.get('url')
        productName = request_body.get('name')
        productImage = request_body.get('img_url')
        productPrice = request_body.get('price')
        productOrigin = request_body.get('sold_by')

        # Save the sign-up data to MySQL database
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO favorites (username, url, productName,productImage,productPrice,productOrigin ) VALUES (%s, %s, %s, %s, %s, %s)",
                [username, url, productName, productImage, productPrice, productOrigin])

        return JsonResponse({'success': True})
    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': ERROR_REQUEST_METHOD})


@csrf_exempt
def get_all_favorites_products(request):
    if request.method == 'GET':
        token = request.headers.get(AUTHORIZATION)
        if not token:
            return JsonResponse({'error': ERROR_MISSING_TOKEN}, status=401)
        try:
            payload = decode(token, SECRET_KEY, algorithms=[HASH_ALGORITHM])
        except InvalidTokenError:
            return JsonResponse({'error': ERROR_INVALID_TOKEN}, status=401)
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
        return JsonResponse({'error': ERROR_REQUEST_METHOD})


@csrf_exempt
def delete_favorite_product(request):
    if request.method == 'DELETE':
        token = request.headers.get(AUTHORIZATION)
        if not token:
            return JsonResponse({'error': ERROR_MISSING_TOKEN}, status=401)
        try:
            payload = decode(token, SECRET_KEY, algorithms=[HASH_ALGORITHM])
        except InvalidTokenError:
            return JsonResponse({'error': ERROR_INVALID_TOKEN}, status=401)
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
        return JsonResponse({'error': ERROR_REQUEST_METHOD})


@csrf_exempt
def add_history(request):
    if request.method == 'POST':
        token = request.headers.get(AUTHORIZATION)
        if not token:
            return JsonResponse({'error': ERROR_MISSING_TOKEN}, status=401)
        try:
            payload = decode(token, SECRET_KEY, algorithms=[HASH_ALGORITHM])
        except InvalidTokenError:
            return JsonResponse({'error': ERROR_INVALID_TOKEN}, status=401)
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
        return JsonResponse({'error': ERROR_REQUEST_METHOD})


def get_history(request):
    if request.method == 'GET':
        token = request.headers.get(AUTHORIZATION)
        if not token:
            return JsonResponse({'error': ERROR_MISSING_TOKEN}, status=401)
        try:
            payload = decode(token, SECRET_KEY, algorithms=[HASH_ALGORITHM])
        except InvalidTokenError:
            return JsonResponse({'error': ERROR_INVALID_TOKEN}, status=401)
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
        return JsonResponse({'error': ERROR_REQUEST_METHOD})


@csrf_exempt
def delete_history(request):
    if request.method == 'DELETE':
        token = request.headers.get(AUTHORIZATION)
        if not token:
            return JsonResponse({'error': ERROR_MISSING_TOKEN}, status=401)
        try:
            payload = decode(token, SECRET_KEY, algorithms=[HASH_ALGORITHM])
        except InvalidTokenError:
            return JsonResponse({'error': ERROR_INVALID_TOKEN}, status=401)
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
        return JsonResponse({'error': ERROR_REQUEST_METHOD})


@csrf_exempt
def edit_user_info(request):
    if request.method == 'POST':
        token = request.headers.get(AUTHORIZATION)
        if not token:
            return JsonResponse({'error': ERROR_MISSING_TOKEN}, status=401)
        try:
            payload = decode(token, SECRET_KEY, algorithms=[HASH_ALGORITHM])
        except InvalidTokenError:
            return JsonResponse({'error': ERROR_INVALID_TOKEN}, status=401)
        username = payload.get('user_id')
        request_body = json.loads(request.body)
        password = request_body.get(PASSWORD)
        email = request_body.get(EMAIL)

        # Save the sign-up data to MySQL database
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password=%s, email=%s WHERE username=%s",
                [password, email, username])

        # Return a JSON response to confirm that the sign-up was successful
        return JsonResponse({'success': True})
    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': ERROR_REQUEST_METHOD})


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        request_body = json.loads(request.body)
        username = request_body.get(USERNAME)
        password = request_body.get(PASSWORD)

        # Check if the user exists in the database
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", [username])
            user = cursor.fetchone()

        # If user exists, verify the password
        if user and (password == user[1]):
            # Generate a JWT token
            token = jwt.encode({'user_id': user[0]}, SECRET_KEY, algorithm=HASH_ALGORITHM)
            # Return the token as a JSON response
            return JsonResponse({'token': token})
        else:
            # Return an error response if the username, email, or password is incorrect
            return JsonResponse({'error': 'Invalid login credentials'})
    else:
        # Return an error response if the request method is not POST
        return JsonResponse({'error': ERROR_REQUEST_METHOD})



@csrf_exempt
def get_email(request):
    if request.method == 'GET':
        token = request.headers.get(AUTHORIZATION)
        if not token:
            return JsonResponse({'error': ERROR_MISSING_TOKEN}, status=401)
        try:
            payload = decode(token, SECRET_KEY, algorithms=[HASH_ALGORITHM])
        except InvalidTokenError:
            return JsonResponse({'error': ERROR_INVALID_TOKEN}, status=401)
        username = payload.get('user_id')
        # Query the database for all favorite products of the user
        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM users WHERE username=%s", [username])
            email = cursor.fetchall()
        # Return the list of favorite products as a JSON response
        return JsonResponse(email, safe=False)
    else:
        # Return an error response for unsupported request methods
        return JsonResponse({'error': ERROR_REQUEST_METHOD})

