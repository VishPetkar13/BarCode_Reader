from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
import cv2 as cv
import flet as ft 
import threading
import base64
import time
from io import BytesIO
from PIL import Image
from database import init_db
from database import save_scan


stopEvent = threading.Event()

#barcodes = set() #not needed anymore 

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
    detected = []

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (5,5), 0)

    _, thresh = cv.threshold(
    gray,
    0,
    255,
    cv.THRESH_BINARY + cv.THRESH_OTSU
    )


    readObj = pyzbar.decode(
        thresh,
        symbols=[
            ZBarSymbol.EAN13,
            ZBarSymbol.CODE128,
            ZBarSymbol.QRCODE,
            ZBarSymbol.UPCA,
            ZBarSymbol.UPCE
        ]
    )

    for obj in readObj:
        barcode_data = obj.data.decode('utf-8')
        barcode_type = obj.type
        detected.append((barcode_data, barcode_type))

    return detected

def videoLoop(imgControl, barcodeText, page):
    cap = cv.VideoCapture(0)

    while cap.isOpened() and not stopEvent.is_set():
        ret, frame = cap.read()
        if not ret:
            break
        codes = readBarcode(frame)
        if codes:
            display_text = []
            for barcode_value, barcode_type in codes:
                save_scan(barcode_value, barcode_type)
                display_text.append(f"{barcode_value} ({barcode_type})")

            barcodeText.value = "\n".join(display_text)
        else:
            barcodeText.value="No Barcode Detected"

        imgControl.src_base64 = f"{openCVToBase64(frame)}"
        page.update()
        time.sleep(0.03)
    cap.release()

def main(page: ft.Page):
    init_db()
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
        #print(barcodes) # This line is not needed anymore

    page.add(
        img, 
        barcodeText, 
        ft.Row([
            ft.ElevatedButton("Start", on_click=startCamera), 
            ft.ElevatedButton("Stop", on_click=stopCamera)  
            ])
    )

ft.app(target=main)
