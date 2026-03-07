from pyzxing import BarCodeReader
import cv2 as cv
import flet as ft
import threading
import base64
import time
from io import BytesIO
from PIL import Image
from database import init_db, save_scan, update_label, get_all_items, delete_scan
from barcode_generator import generate_barcode

# ─────────────────────────────────────────────
#  GLOBALS
# ─────────────────────────────────────────────
stopEvent = threading.Event()
latest_frame = None
reader = BarCodeReader()

# ─────────────────────────────────────────────
#  DESIGN TOKENS  (one place to change colours)
# ─────────────────────────────────────────────
# Think of these like CSS variables. Defining colours/sizes in one place
# means you only need to edit here to retheme the entire app.
BG_DARK      = "#0D0D0D"   # near-black background
BG_CARD      = "#1A1A1A"   # slightly lighter for cards / panels
BG_SURFACE   = "#242424"   # input fields, containers
ACCENT       = "#FF6B00"   # amber-orange — the "LED readout" colour
ACCENT_DARK  = "#CC5500"   # darker shade for pressed states
TEXT_PRIMARY = "#F0F0F0"   # off-white — easier on eyes than pure white
TEXT_MUTED   = "#888888"   # secondary text (timestamps, hints)
DANGER       = "#E53935"   # delete / destructive actions
BORDER       = "#2E2E2E"   # subtle borders between elements

# ─────────────────────────────────────────────
#  HELPER: OpenCV frame  →  base64 JPEG string
# ─────────────────────────────────────────────
def openCVToBase64(frame):
    """
    Flet's Image control can't show a raw OpenCV frame directly.
    We need to convert it through a chain:
      OpenCV (BGR numpy array)
        → RGB numpy array      (PIL expects RGB, not BGR)
        → PIL Image object
        → JPEG bytes in memory (BytesIO — no temp file needed)
        → base64 string        (Flet Image.src_base64 accepts this)
    """
    frameRGB = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    pilImg   = Image.fromarray(frameRGB)
    buffer   = BytesIO()
    pilImg.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# ─────────────────────────────────────────────
#  HELPER: Decode a barcode from a saved frame
# ─────────────────────────────────────────────
def readBarcode(frame):
    """
    ZXing (pyzxing) can't read a raw numpy array — it needs a file path.
    So we save the frame as temp.jpg first, then point ZXing at it.
    The 'raw' field is bytes, so we decode() it to a regular string.
    We filter out results shorter than 10 chars to drop partial/noisy reads.
    """
    cv.imwrite("temp.jpg", frame)
    results  = reader.decode("temp.jpg")
    detected = []

    if results:
        for res in results:
            if "raw" in res and "format" in res:
                barcode_value = res["raw"].decode("utf-8")
                barcode_type  = res["format"].decode("utf-8")
                if len(barcode_value) > 10:
                    detected.append((barcode_value, barcode_type))

    return detected


# ─────────────────────────────────────────────
#  CAMERA LOOP  (runs in background thread)
# ─────────────────────────────────────────────
def videoLoop(imgControl, page):
    """
    This function runs in a separate thread so the UI stays responsive.

    Key concept — threading:
      The GUI runs on the 'main' thread. If we put a tight camera loop
      there, the UI would freeze. By running videoLoop in a daemon thread
      (daemon=True means it auto-dies when the main program exits) we
      keep the camera separate from the UI.

    stopEvent is a threading.Event(). Calling stopEvent.set() from the
    main thread signals this loop to exit cleanly.
    """
    global latest_frame
    cap = cv.VideoCapture(0)

    while cap.isOpened() and not stopEvent.is_set():
        ret, frame = cap.read()
        if not ret:
            break

        latest_frame          = frame.copy()
        imgControl.src_base64 = openCVToBase64(frame)
        page.update()
        time.sleep(0.03)   # ~33 fps cap — enough for smooth preview

    cap.release()


# ─────────────────────────────────────────────
#  REUSABLE UI COMPONENTS
# ─────────────────────────────────────────────
def make_header(title: str, subtitle: str = "") -> ft.Container:
    """
    Returns the top header bar used on every page.
    Encapsulating it in a function means we write it once and reuse it.
    """
    children = [
        ft.Text(
            "◈ BARCODE VAULT",
            size=11,
            color=ACCENT,
            font_family="monospace",
            weight=ft.FontWeight.BOLD,
        ),
        ft.Text(
            title,
            size=22,
            color=TEXT_PRIMARY,
            weight=ft.FontWeight.BOLD,
        ),
    ]
    if subtitle:
        children.append(ft.Text(subtitle, size=12, color=TEXT_MUTED))

    return ft.Container(
        content=ft.Column(children, spacing=2),
        padding=ft.padding.only(left=20, top=20, right=20, bottom=16),
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
    )


def make_pill_button(
    label: str,
    on_click,
    icon=None,
    bgcolor: str = BG_SURFACE,
    color: str = TEXT_PRIMARY,
    expand: bool = False,
) -> ft.Container:
    """
    A styled button that looks like a pill / chip.
    Flet's ElevatedButton has limited styling options, so we build our
    own using Container + GestureDetector logic via on_click on Container.

    Parameters:
      label   — button text
      on_click — function called when tapped
      icon    — optional ft.Icons constant
      bgcolor  — background colour (defaults to surface grey)
      color   — text/icon colour
      expand  — whether it stretches to fill available width
    """
    content_children = []
    if icon:
        content_children.append(ft.Icon(icon, color=color, size=16))
    content_children.append(
        ft.Text(label, color=color, size=13, weight=ft.FontWeight.BOLD)
    )

    return ft.Container(
        content=ft.Row(
            content_children,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        ),
        bgcolor=bgcolor,
        border_radius=30,
        padding=ft.padding.symmetric(horizontal=20, vertical=12),
        on_click=on_click,
        expand=expand,
    )


def make_history_card(
    display: str,
    scan_time: str,
    on_click,
) -> ft.Container:
    """
    A single card in the history list.
    Each card shows the label (or barcode value) and the scan timestamp.
    The left orange bar is a visual accent — common in material-style cards.
    """
    return ft.Container(
        content=ft.Row(
            [
                # Left accent bar
                ft.Container(width=3, height=50, bgcolor=ACCENT, border_radius=2),
                ft.Container(width=12),   # spacer
                ft.Column(
                    [
                        ft.Text(
                            display,
                            size=15,
                            color=TEXT_PRIMARY,
                            weight=ft.FontWeight.BOLD,
                            overflow="ellipsis",
                            max_lines=1,
                        ),
                        ft.Text(
                            f"📅  {scan_time}",
                            size=11,
                            color=TEXT_MUTED,
                        ),
                    ],
                    spacing=4,
                    expand=True,
                ),
                ft.Icon(ft.icons.CHEVRON_RIGHT, color=TEXT_MUTED, size=18),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=BG_CARD,
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
        on_click=on_click,
        border=ft.border.all(1, BORDER),
        margin=ft.margin.only(bottom=8),
    )


# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
def main(page: ft.Page):
    init_db()

    # ── Page-level settings ──────────────────
    # theme_mode DARK means Flet's default widgets also go dark.
    # bgcolor sets the canvas behind all our views.
    page.title            = "Barcode Vault"
    page.theme_mode       = ft.ThemeMode.DARK
    page.bgcolor          = BG_DARK
    page.window_width     = 420    # portrait-phone-like on desktop
    page.window_height    = 780
    page.window_resizable = True
    page.padding          = 0      # we'll control padding per-view

    # ── Shared controls ──────────────────────
    # img lives here (not inside route_change) so the camera thread always
    # has a valid reference to update — even across route changes.
    img = ft.Image(
        width=380,
        height=250,
        fit="cover",
        border_radius=12,
        src="/placeholder",   # avoids "missing src" error before camera starts
    )

    threadHolder = {"thread": None}

    # ── Camera controls ──────────────────────
    def startCamera(e=None):
        if threadHolder["thread"] and threadHolder["thread"].is_alive():
            return
        stopEvent.clear()
        t = threading.Thread(
            target=videoLoop, args=(img, page), daemon=True
        )
        t.start()
        threadHolder["thread"] = t

    def stopCamera(e=None):
        stopEvent.set()

    def captureBarcode(e):
        global latest_frame
        if latest_frame is None:
            show_snack("⚠  Start the camera first", color=DANGER)
            return

        codes = readBarcode(latest_frame)
        if codes:
            for barcode_value, barcode_type in codes:
                save_scan(barcode_value, barcode_type)
                ask_for_label(barcode_value)
        else:
            show_snack("No barcode detected — try again")

    # ── Utility ─────────────────────────────
    def show_snack(message: str, color: str = ACCENT):
        """
        SnackBar is Flet's toast-style notification at the bottom of the screen.
        We create a helper so we don't repeat the styling everywhere.
        """
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=BG_DARK, weight=ft.FontWeight.BOLD),
            bgcolor=color,
            duration=2500,
        )
        page.snack_bar.open = True
        page.update()

    def go_back(e=None):
        if len(page.views) > 1:
            page.views.pop()
            page.update()

    # ── Label dialog ─────────────────────────
    def ask_for_label(barcode_value: str):
        """
        After a successful scan, we pop a dialog asking the user to name it.
        If they cancel, the scan is deleted — we don't want unlabelled noise
        building up in the database.
        """
        def save_label(e):
            label = input_field.value.strip() or barcode_value
            update_label(barcode_value, label)
            dialog.open = False
            page.update()
            show_snack(f"✓  Saved as '{label}'")

        def cancel_label(e):
            delete_scan(barcode_value)
            dialog.open = False
            page.update()

        input_field = ft.TextField(
            label="Store / receipt name",
            border_color=ACCENT,
            focused_border_color=ACCENT,
            cursor_color=ACCENT,
            color=TEXT_PRIMARY,
            bgcolor=BG_SURFACE,
            border_radius=10,
        )

        dialog = ft.AlertDialog(
            title=ft.Text(
                "Name this scan",
                color=TEXT_PRIMARY,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                width=320,
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Text(
                                barcode_value,
                                font_family="monospace",
                                size=12,
                                color=ACCENT,
                            ),
                            bgcolor=BG_SURFACE,
                            border_radius=8,
                            padding=10,
                        ),
                        ft.Container(height=12),
                        input_field,
                    ],
                    tight=True,
                    spacing=0,
                ),
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    style=ft.ButtonStyle(color=TEXT_MUTED),
                    on_click=cancel_label,
                ),
                ft.TextButton(
                    "Save",
                    style=ft.ButtonStyle(color=ACCENT),
                    on_click=save_label,
                ),
            ],
        )

        page.dialog = dialog
        dialog.open = True
        page.update()

    # ── Delete dialog ────────────────────────
    def confirm_delete(value: str):
        def do_delete(e):
            delete_scan(value)
            dialog.open = False
            page.views.pop()          # leave /view
            page.go("/history")       # refresh history
            show_snack("🗑  Barcode deleted", color=DANGER)

        def close_dialog(e=None):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Delete barcode?", color=DANGER, weight=ft.FontWeight.BOLD),
            content=ft.Text(
                "This will permanently remove the barcode from your vault.",
                color=TEXT_MUTED,
                size=13,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    style=ft.ButtonStyle(color=TEXT_MUTED),
                    on_click=close_dialog,
                ),
                ft.TextButton(
                    "Delete",
                    style=ft.ButtonStyle(color=DANGER),
                    on_click=do_delete,
                ),
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    # ── Barcode viewer ───────────────────────
    def show_saved_barcode(value: str, typ: str, label: str):
        img_base64 = generate_barcode(value, typ)

        page.views.append(
            ft.View(
                "/view",
                bgcolor=BG_DARK,
                padding=0,
                controls=[
                    make_header(label or value, "Tap barcode to zoom"),

                    # Barcode image in a centred card
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Image(
                                    src_base64=img_base64,
                                    width=360,
                                    fit="contain",
                                    border_radius=12,
                                ),
                                ft.Container(height=8),
                                ft.Text(
                                    value,
                                    font_family="monospace",
                                    size=11,
                                    color=TEXT_MUTED,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=BG_CARD,
                        border_radius=16,
                        padding=20,
                        margin=ft.margin.symmetric(horizontal=20, vertical=16),
                        border=ft.border.all(1, BORDER),
                    ),

                    # Action buttons
                    ft.Container(
                        content=ft.Row(
                            [
                                make_pill_button(
                                    "Back",
                                    on_click=go_back,
                                    icon=ft.icons.ARROW_BACK,
                                    expand=True,
                                ),
                                ft.Container(width=12),
                                make_pill_button(
                                    "Delete",
                                    on_click=lambda e: confirm_delete(value),
                                    icon=ft.icons.DELETE_OUTLINE,
                                    bgcolor=DANGER,
                                    color="#FFFFFF",
                                    expand=True,
                                ),
                            ]
                        ),
                        padding=ft.padding.symmetric(horizontal=20),
                    ),
                ],
            )
        )
        page.update()

    # ── Route handler ────────────────────────
    def route_change(route):
        """
        Flet's routing works by maintaining a stack of Views.
        Each time the route changes we clear the stack and rebuild it.

        Why clear and rebuild?
        Because Flet doesn't hot-reload views — the data in history could
        have changed (new scan, deletion), so we always fetch fresh.
        """
        page.views.clear()

        # ── / — Scanner ──────────────────────
        if page.route == "/":
            page.views.append(
                ft.View(
                    "/",
                    bgcolor=BG_DARK,
                    padding=0,
                    controls=[
                        make_header("Scanner", "Align barcode then tap Capture"),

                        # Camera preview
                        ft.Container(
                            content=img,
                            alignment=ft.alignment.center,
                            bgcolor=BG_CARD,
                            border_radius=16,
                            margin=ft.margin.symmetric(horizontal=20, vertical=12),
                            padding=8,
                            border=ft.border.all(1, BORDER),
                            # Scan-line overlay hint
                            # (a thin accent line across the middle)
                        ),

                        # Tip text
                        ft.Container(
                            content=ft.Text(
                                "Position barcode within the frame",
                                size=12,
                                color=TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            alignment=ft.alignment.center,
                        ),

                        ft.Container(height=16),

                        # Camera control buttons — row of 3
                        ft.Container(
                            content=ft.Row(
                                [
                                    make_pill_button(
                                        "Start",
                                        on_click=startCamera,
                                        icon=ft.icons.VIDEOCAM,
                                        bgcolor=BG_SURFACE,
                                        expand=True,
                                    ),
                                    ft.Container(width=8),
                                    make_pill_button(
                                        "Capture",
                                        on_click=captureBarcode,
                                        icon=ft.icons.CROP_FREE,
                                        bgcolor=ACCENT,
                                        color=BG_DARK,
                                        expand=True,
                                    ),
                                    ft.Container(width=8),
                                    make_pill_button(
                                        "Stop",
                                        on_click=stopCamera,
                                        icon=ft.icons.STOP_CIRCLE_OUTLINED,
                                        bgcolor=BG_SURFACE,
                                        expand=True,
                                    ),
                                ],
                            ),
                            padding=ft.padding.symmetric(horizontal=20),
                        ),

                        ft.Container(height=16),

                        # History navigation — full-width accent button
                        ft.Container(
                            content=make_pill_button(
                                "View Saved Barcodes",
                                on_click=lambda e: page.go("/history"),
                                icon=ft.icons.HISTORY,
                                bgcolor=BG_CARD,
                                color=ACCENT,
                                expand=True,
                            ),
                            padding=ft.padding.symmetric(horizontal=20),
                        ),
                    ],
                )
            )

        # ── /history — Saved scans ────────────
        elif page.route == "/history":
            items = get_all_items()

            if items:
                history_controls = []
                for barcode_value, barcode_type, user_label, scan_time in items:
                    display = user_label if user_label else barcode_value
                    history_controls.append(
                        make_history_card(
                            display=display,
                            scan_time=scan_time,
                            on_click=lambda e, v=barcode_value, t=barcode_type, l=user_label: show_saved_barcode(v, t, l),
                        )
                    )

                history_content = ft.Column(
                    history_controls,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=0,
                )
            else:
                # Empty state — better UX than a blank screen
                history_content = ft.Column(
                    [
                        ft.Container(height=60),
                        ft.Icon(ft.icons.INBOX_OUTLINED, size=56, color=TEXT_MUTED),
                        ft.Container(height=12),
                        ft.Text(
                            "No barcodes saved yet",
                            color=TEXT_MUTED,
                            size=15,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Go back and scan your first receipt",
                            color=TEXT_MUTED,
                            size=12,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )

            page.views.append(
                ft.View(
                    "/history",
                    bgcolor=BG_DARK,
                    padding=0,
                    controls=[
                        make_header(
                            "Vault",
                            f"{len(items)} barcode{'s' if len(items) != 1 else ''} stored",
                        ),
                        ft.Container(
                            content=history_content,
                            expand=True,
                            padding=ft.padding.symmetric(horizontal=20, vertical=12),
                        ),
                        ft.Container(
                            content=make_pill_button(
                                "Back to Scanner",
                                on_click=lambda e: page.go("/"),
                                icon=ft.icons.ARROW_BACK,
                                expand=True,
                            ),
                            padding=ft.padding.symmetric(horizontal=20, vertical=12),
                            border=ft.border.only(top=ft.BorderSide(1, BORDER)),
                        ),
                    ],
                )
            )

        page.update()

    page.on_route_change = route_change
    page.go("/")


ft.app(target=main)