from pyzbar import pyzbar
import cv2 as cv
import flet as ft 
import threading
import base64
import time
from io import BytesIO
from PIL import Image

stopEvent = threading.Event()

barCodes = ()

def openCVToBase64(frame):
    """ This function will take in a frame from the camera (opencv) and 
    convert it to a base64 encode jpeg stream which can be used to display
    in the flet image control"""

    frameRGB = cv.cvtColor(frame, cv.COLOR_BGR2RGB) #convertiing 
