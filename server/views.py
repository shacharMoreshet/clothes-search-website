import argparse
from django.http import JsonResponse
from predict import main


def get_image(request):
    image_url = request.GET.get('image_url')
    args = argparse.Namespace(encoder_path='encoder-12-1170.ckpt',
                              vocab_path1='json/train_up_vocab.pkl',
                              vocab_path2='clothing_vocab_accessory2.pkl',
                              confidence=0.5,
                              nms_thresh=0.4,
                              cfg_file='cfg/yolov3.cfg',
                              weights_file='yolov3.weights',
                              reso='832',
                              scales='1,2,3',
                              embed_size=256,
                              hidden_size=512,
                              num_layers=1,
                              roi_size=13,
                              img_url=image_url)
    res = main(args)
    return JsonResponse(res)
