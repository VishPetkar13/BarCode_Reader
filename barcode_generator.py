import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64

def generate_barcode(barcode_value, barcode_type):

    format_map = {
        "EAN_13": "ean13",
        "UPC_A": "upca",
        "CODE_128": "code128",
        "ITF": "itf"
    }

    try: 
        barcode_type = format_map.get(barcode_type, barcode_type)
        
        barcode_class = barcode.get_barcode_class(barcode_type)

        buffer = BytesIO()

        my_barcode = barcode_class(barcode_value, writer=ImageWriter())
        my_barcode.write(buffer)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    except Exception as e:
        print("Error generating barcode:", e)
        return None