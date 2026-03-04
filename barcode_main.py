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
from database import get_all_items
from database import delete_scan


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

    # itemList = ft.ListView(expand=True, spacing=10, auto_scroll=True)
    # barcodeImage = ft.Image(width=400, height=150, src=" ")
    img = ft.Image(width=480, height=320, src=" ")
    barcodeText = ft.Text("No barcode detected", size=16, selectable=True)

    threadHolder = {"thread": None}

    def route_change(route):
        page.views.clear()
        if page.route =="/":
            page.views.append(
                ft.View(
                    "/",
                    [
                        img,
                        barcodeText,
                        ft.Row([
                            ft.ElevatedButton("Start", on_click=startCamera),
                            ft.ElevatedButton("Capture", on_click=captureBarcode),
                            ft.ElevatedButton("Stop", on_click=stopCamera),
                            ft.ElevatedButton("History", on_click=lambda e: page.go("/history"))
                            
                        ])
                    ]
                )
            )
        if page.route == "/history":
            items = get_all_items()
            history_controls = []
            
            for barcode_value, barcode_type, user_label, scan_time in items:
                display = user_label if user_label else barcode_value

                history_controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(display, size=16, weight="bold"),
                                ft.Text(f"Scanned: {scan_time}", size=12, color="gray"),
                            ]
                        ),
                        on_click=lambda e, val= barcode_value, typ= barcode_type: show_saved_barcode(val, typ),
                        padding=10
                    )
                    
                        
                    )
                    
            page.views.append(
                ft.View(
                    "/history",
                    [
                        ft.Text("Scan History", size=20, weight="bold"),

                        ft.Container(
                            expand=True, 
                            content= ft.Column(history_controls, scroll=ft.ScrollMode.AUTO)
                        ),
                        
                        ft.ElevatedButton("Back", on_click=lambda e: page.go("/")) 
                    ]
                )
            )        
        page.update()


    def show_saved_barcode(value, typ):
        img_base64 = generate_barcode(value, typ)

        def confirm_delete(e):
            
            def delete_items(e):
                delete_scan(value)

                dialog.open = False
                page.snack_bar = ft.SnackBar(ft.Text("Barcode deleted"))
                page.snack_bar.open = True
                page.go("/history")
                page.update()

            dialog = ft.AlertDialog(
                title=ft.Text("Delete this barcode?"),
                content=ft.Text("This cannot be undone."),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
                    ft.TextButton("Delete", on_click=delete_items),
                ]
            )

            page.dialog = dialog
            dialog.open = True
            page.update()

        def close_dialog():
            page.dialog.open = False
            page.update()

        page.views.append(
            ft.View(
                "/view",
                [
                    ft.Image(src_base64=img_base64),
                    ft.Row(
                        [
                            ft.ElevatedButton("Back", on_click=lambda e: go_back()),
                            ft.ElevatedButton("Delete", color="white", bgcolor="red", on_click=confirm_delete)
                        ]
                    )
                ]
            )
        )
        page.update()

    def go_back():
        if len(page.views)>1:
            page.views.pop()
            page.update()

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
        barcodeText.value = "Stopped"
        page.update()
        #print(barcodes) # This line is not needed anymore

    
    def ask_for_label(barcode_value):

        def save_label(e):
            label = input_field.value
            update_label(barcode_value, label)
            dialog.open = False
            page.update()

        def cancel_label(e):
            delete_scan(barcode_value)
            dialog.open = False
            page.update()

        input_field = ft.TextField(label="Enter Store name")

        dialog = ft.AlertDialog(
            title=ft.Text("Name this bill"),
            content=ft.Container( 
                width=350,
            content=ft.Column(
                [
                    ft.Text(f"Barcode: {barcode_value}", size=14, selectable=True),
                    input_field
                ], 
                tight=True
            )
            ),
            actions=[
                ft.TextButton("Save", on_click=save_label),
                ft.TextButton("Cancel", on_click=cancel_label)
                
            ]
        )

        page.dialog = dialog
        dialog.open = True
        page.update()

    # def showBarcode(e):
    #     test_value = "00010521435150001121625005"
    #     test_type  = "ITF"

    #     img_base64 = generate_barcode(test_value, test_type)

    #     if img_base64:
    #         barcodeImage.src_base64 = img_base64
    #         page.update()  

    # def loadHistory(e):

    #     itemList.controls.clear()

    #     items = get_all_items()

    #     for barcode_value, barcode_type, user_label in items:

    #         display_name = user_label if user_label else barcode_value

    #         def show_saved(e, val=barcode_value, typ=barcode_type):
    #             img_base64 = generate_barcode(val, typ)
    #             if img_base64:
    #                 barcodeImage.src_base64 = img_base64
    #                 page.update()

    #         itemList.controls.append(
    #             ft.TextButton(
    #                 text=display_name,
    #                 on_click=show_saved
    #             )
    #         )

    #     page.update()

    # page.add(
    #     ft.Column(
    #         [
                   
    #             img, 
    #             barcodeText,
    #             barcodeImage,
    #             ft.Container(
    #                 height = 200,
    #                 content = itemList
    #             ),
    #             ft.Row([
    #                 ft.ElevatedButton("Start", on_click=startCamera),
    #                 ft.ElevatedButton("Capture", on_click=captureBarcode),
    #                 ft.ElevatedButton("Load History", on_click=loadHistory), 
    #                 ft.ElevatedButton("Stop", on_click=stopCamera)  
    #                 ])
    #         ],
    #         scroll = ft.ScrollMode.AUTO
    # )
    # )
    page.on_route_change = route_change
    page.go("/")

ft.app(target=main)
