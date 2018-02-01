""" Module to cash all the images that are used several times"""
import logging

import cv2

imagePath = "analysis/images/"
LOAD_IMAGE_COLOR = 1
LOAD_IMAGE_GRAYSCALE = 0
LOAD_IMAGE_ALPHA_CHANNEL = -1

imgDict = {}
# images on disk
mask_bot = imagePath + 'mask_bot.jpg'
mask_mid = imagePath + 'mask_mid.jpg'
mask_top = imagePath + 'mask_top.jpg'
mask_cabins = imagePath + 'mask_cabins.jpg'
mask_right = imagePath + 'mask_right.jpg'
mask_cashier = imagePath + 'mask_cashier.jpg'
mask_main = imagePath + 'mask_main.jpg'
white = imagePath + 'white.png'
inferno_cropped = imagePath + 'inferno_cropped.jpg'

# cached images (should not be written)
_colored_heatmap = 'colored_heatmap.png'


def load():
    imgGrayTuple = (mask_bot, mask_mid, mask_top, mask_cabins, mask_right, mask_cashier, mask_main, white)
    imgColTuple = (inferno_cropped, )

    #for grayscale
    for path in imgGrayTuple:
        imgDict[path] = cv2.imread(path, LOAD_IMAGE_GRAYSCALE)

    #for color
    for path in imgColTuple:
        imgDict[path] = cv2.imread(path, LOAD_IMAGE_COLOR)


def get(imgPath):
    return imgDict[imgPath]

def getBufferedImage(name):
    img = imgDict[name]
    try:
        retval, buf = cv2.imencode('.png', img, [cv2.IMWRITE_PNG_COMPRESSION, 1])
    except Exception as e:
        logging.error("could not load image")
        return 0

    return buf

def put(name, img):
    imgDict[name] = img