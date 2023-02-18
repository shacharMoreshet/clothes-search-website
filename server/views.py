import argparse
from django.http import JsonResponse
from predict import main


def get_image(request):
    image_url = request.GET.get('image_url')
    res = main(image_url)
    return JsonResponse(res)
