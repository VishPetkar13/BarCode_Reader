# from pyzbar import pyzbar
# from pyzbar.pyzbar import ZBarSymbol
from pyzxing import BarCodeReader
import cv2 as cv
import flet as ft 
import threading
import base64
import time
from io import BytesIO
from PIL import Image
from database import init_db
from database import save_scan
from database import update_label
from barcode_generator import generate_barcode


stopEvent = threading.Event()
recent_scans = {}
latest_frame = None
SCAN_DELAY = 3
reader = BarCodeReader() #the startup for this is heavy on the system; so created once globally.
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
     # save frame temporarily for ZXing
    cv.imwrite("temp.jpg", frame)

    results = reader.decode("temp.jpg")

    detected = []

    if results:
        for res in results:
            if 'raw' in res and 'format' in res:

                barcode_value = res['raw'].decode('utf-8')
                barcode_type  = res['format'].decode('utf-8')

                # ignore partial short reads
                if len(barcode_value) > 10:
                    detected.append((barcode_value, barcode_type))

    return detected

def videoLoop(imgControl, barcodeText, page):
    global recent_scans
    cap = cv.VideoCapture(0)

    while cap.isOpened() and not stopEvent.is_set():
        ret, frame = cap.read()
        global latest_frame
        if not ret:
            break
        # codes = readBarcode(frame)
        # current_time = time.time()
        # if codes:
        #     display_text = []
        #     for barcode_value, barcode_type in codes:
        #         # check if recently scanned
        #         if barcode_value in recent_scans:
        #             last_seen = recent_scans[barcode_value]
        #             if current_time - last_seen < SCAN_DELAY:
        #                 continue   # ignore duplicate frame

        #         # accept new scan
        #         recent_scans[barcode_value] = current_time
        #         save_scan(barcode_value, barcode_type)

        #         display_text.append(f"{barcode_value} ({barcode_type})")

        #     if display_text:
        #         barcodeText.value = "\n".join(display_text)
        # else:
        #     barcodeText.value = "No Barcode Detected"
        latest_frame = frame.copy()
        imgControl.src_base64 = f"{openCVToBase64(frame)}"
        page.update()
        time.sleep(0.03)
    cap.release()

def main(page: ft.Page):
    init_db()
    page.window_width = 640
    page.window_height = 800

    barcodeImage = ft.Image(width=400, height=150, src="")
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

    def captureBarcode(e):

        global latest_frame

        if latest_frame is None:
            barcodeText.value = "No Frame Captured"
            page.update()
            return

        codes = readBarcode(latest_frame)

        if codes:
            display_text = []

            for barcode_value, barcode_type in codes:
                save_scan(barcode_value, barcode_type)
                ask_for_label(barcode_value)
                display_text.append(f"{barcode_value} ({barcode_type})")

            barcodeText.value = "\n".join(display_text)
        else:
            barcodeText.value = "No Barcode Detected"

        page.update()


    def stopCamera(e):
        stopEvent.set()
        barcodeText.value = "stopped"
        page.update()
        #print(barcodes) # This line is not needed anymore

    
    def ask_for_label(barcode_value):

        def save_label(e):
            label = input_field.value
            update_label(barcode_value, label)
            dialog.open = False
            page.update()

        input_field = ft.TextField(label="Enter Store name")

        dialog = ft.AlertDialog(
            title=ft.Text("Name this Bill"),
            content=input_field,
            actions=[
                ft.TextButton("Save", on_click=save_label)
            ]
        )

        page.dialog = dialog
        dialog.open = True
        page.update()

    def showBarcode(e):
        test_value = "00010521435150001121625005"
        test_type  = "ITF"

        img_base64 = generate_barcode(test_value, test_type)

        if img_base64:
            barcodeImage.src_base64 = img_base64
            page.update()  

    page.add(
        img, 
        barcodeText,
        barcodeImage, 
        ft.Row([
            ft.ElevatedButton("Start", on_click=startCamera),
            ft.ElevatedButton("Capture", on_click=captureBarcode),
            ft.ElevatedButton("Show Barcode", on_click=showBarcode), 
            ft.ElevatedButton("Stop", on_click=stopCamera)  
            ])
    )

ft.app(target=main)
