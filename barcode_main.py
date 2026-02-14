from pyzbar import pyzbar
import cv2 as cv
import flet as ft 
import threading
import base64
import time
from io import BytesIO
from PIL import Image

stopEvent = threading.Event()

barcodes = set()

def openCVToBase64(frame):
    """ This function will take in a frame from the camera (opencv) and 
    convert it to a base64 encode jpeg stream which can be used to display
    in the flet image control"""

    frameRGB = cv.cvtColor(frame, cv.COLOR_BGR2RGB) #converting BGR (openCV) to RGB (pillow)
    pilImg = Image.fromarray(frameRGB)
    buffer=BytesIO()
    pilImg.save(buffer, format='JPEG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def readBarcode(frame):
    readObj = pyzbar.decode(frame)
    for obj in readObj:
        barcodes.add(obj.data.decode('utf-8'))
    return barcodes

def videoLoop(imgControl, barcodeText, page):
    cap = cv.VideoCapture(0)

    while cap.isOpened() and not stopEvent.is_set():
        ret, frame = cap.read()
        if not ret:
            break
        barcodes = readBarcode(frame)
        if barcodes:
            barcodeText.value = "\n".join(barcodes)
        else:
            barcodeText.value="No Barcode Detected"

        imgControl.src_base64 = f"{openCVToBase64(frame)}"
        page.update()
        time.sleep(0.03)
    cap.release()

def main(page: ft.Page):
    page.window_width = 640
    page.window_height = 800

    img = ft.Image(width=480, height=320, src="localhost/nothing.jpg")
    barcodeText = ft.Text("No barcode detected", size=16, selectable=True)

    threadHolder = {"thread": None}

    def startCamera(e):
        if threadHolder["thread"] and threadHolder["thread"].is_alive():
            return 
        stopEvent.clear()

        t = threading.Thread(target=videoLoop, args=(img, barcodeText, page), daemon=True)
        t.start()
        threadHolder["thread"] = t

    def stopCamera(e):
        stopEvent.set()
        barcodeText.value = "stopped"
        page.update()
        print(barcodes)

    page.add(
        img, 
        barcodeText, 
        ft.Row([
            ft.Button("Start", on_click=startCamera), 
            ft.Button("Stop", on_click=stopCamera) 
            ])
    )

ft.run(main)
