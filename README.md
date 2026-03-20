# Barcode Reader & Digital Receipt Manager

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Flet](https://img.shields.io/badge/GUI-Flet-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Project Type](https://img.shields.io/badge/Project-Portfolio%20Project-purple)

A **desktop barcode scanning and digital receipt management application** built with **Python, OpenCV, ZXing, SQLite, and Flet**.

The application allows users to:

* Scan retail barcodes using a webcam
* Store them locally in a SQLite database
* Label them for easy identification
* Search and retrieve them when returning items
* Track return window expiry dates with colour coded status
* Delete them when no longer needed

This project demonstrates **end-to-end Python application development**, including **computer vision, database management, GUI development, and multi-threaded processing**.

---

# Recruiter / Portfolio Summary

This project demonstrates practical software engineering skills relevant to **Data Engineering, Python Development, and Applied Machine Learning environments**.

### Key Competencies Demonstrated

* Python application development
* Computer vision with OpenCV
* Barcode detection using ZXing
* Desktop GUI development using Flet
* SQLite database design, persistence, and schema migration
* Multi-threaded programming
* UI/UX design with a custom component system
* Real-time data filtering and search
* Expiry tracking and colour coded status indicators
* Data storage and retrieval workflows
* Cross-library integration and compatibility handling

### Engineering Highlights

* Implemented **real-time barcode scanning** via webcam using OpenCV.
* Integrated **ZXing barcode detection** to improve accuracy over alternative libraries.
* Designed a **SQLite database schema** for persistent barcode storage.
* Built an **interactive GUI desktop application** using Flet with a fully custom dark theme.
* Implemented **threaded camera processing** to prevent UI blocking.
* Created a **reusable component architecture** using design tokens and component functions.
* Developed a **live search and filter system** for the history page with case-insensitive matching.
* Implemented a **non-destructive database migration** to add new columns without losing existing data.
* Built an **expiry tracking system** with colour coded status indicators per barcode.
* Created a **format translation layer** to resolve compatibility differences between barcode libraries.
* Developed **barcode regeneration functionality** using python-barcode.

---

# Project Motivation

Retail stores often print **return barcodes on receipts or clothing tags** that are required for refunds or exchanges within a limited period (commonly **28 days**).

These barcodes are easy to **lose or damage**.

This application provides a digital solution where users can:

* Scan and store return barcodes
* Label them for easy identification
* Track how many days remain before the return window closes
* Search and retrieve them when returning items
* Delete them once they are no longer needed

---

# Features

## Barcode Scanning

Uses a **webcam** to capture frames and detect barcodes.

### Technologies used

* **OpenCV** for camera capture
* **ZXing (via pyzxing)** for barcode decoding

To prevent partial scans, the application allows the user to **manually capture the frame** instead of continuously scanning.

### Supported Barcode Formats

* EAN-13
* UPC-A
* CODE-128
* ITF

---

## Persistent Storage

All scanned barcodes are stored in a **local SQLite database**.

### Database Schema

| Field         | Description                         |
| ------------- | ----------------------------------- |
| id            | Auto-increment primary key          |
| barcode_value | Raw barcode data                    |
| barcode_type  | Barcode format                      |
| user_label    | User-defined label                  |
| scan_time     | Timestamp of scan                   |
| return_window | Return window in days (default: 28) |

Duplicate barcodes are prevented using a **UNIQUE constraint on `barcode_value`**.

---

## Labeling System

After scanning a barcode, the user is prompted to **name it**.

Example labels:

* Blue Hoodie
* Black Jeans
* Winter Jacket

Users can also **cancel the labeling process**, which removes the scan from the database.

---

## Search and Filter

The history page includes a **live search bar** that filters saved barcodes in real time as the user types.

* Matches against both the user label and the raw barcode value
* Case-insensitive matching
* Filters the in-memory list without re-querying the database on every keystroke

---

## Expiry Tracking

Each barcode has a **return window** (defaulting to 28 days) tracked from the scan date.

The history page displays a **colour coded expiry status** on every card:

| Status  | Colour | Condition                  |
| ------- | ------ | -------------------------- |
| Safe    | Green  | More than 7 days remaining |
| Warning | Amber  | 1 to 7 days remaining      |
| Expired | Red    | 0 days remaining           |

Days remaining are **calculated at runtime** from the scan timestamp — no stale stored values.

---

## Barcode Regeneration

Saved barcodes can be regenerated and displayed using the **python-barcode** library.

Since **ZXing** and **python-barcode** use different naming conventions, a **format translation layer** was implemented.

### Format Mapping

| ZXing Format | python-barcode Format |
| ------------ | --------------------- |
| EAN_13       | ean13                 |
| UPC_A        | upca                  |
| CODE_128     | code128               |
| ITF          | itf                   |

This ensures compatibility between the **scanner and generator libraries**.

---

## Scan History

The application includes a **History page** displaying previously scanned barcodes.

Each entry shows:

* Item label
* Scan timestamp
* Colour coded days remaining

History is automatically **sorted by most recent scans first** and is fully searchable.

Users can **tap any item** to view the stored barcode.

---

## Barcode Viewer

Selecting a saved item opens a screen displaying the **reconstructed barcode**.

From this screen users can:

* Go back to history
* Delete the barcode

---

## Delete Functionality

Users can remove stored barcodes when they are **no longer needed**.

Example use case: a store's **return window has expired** and the barcode is no longer required.

The delete feature includes:

* Confirmation dialog
* Immediate database removal
* Automatic history refresh
* Snackbar notification for user feedback

---

## UI Design System

The application uses a **custom dark industrial theme** designed to feel like a native mobile app on desktop.

Key design decisions:

* Named colour tokens for consistent theming across all screens
* Reusable component functions (`make_header`, `make_pill_button`, `make_history_card`) following a DRY architecture
* Portrait window dimensions to reflect the app's mobile target
* Empty state handling for a polished user experience
* Semantic colour system for expiry status (green, amber, red)

---

## Threaded Camera Processing

The webcam feed runs inside a **separate thread**.

This prevents the **user interface from freezing** while capturing video frames.

### Benefits

* Smooth UI responsiveness
* Continuous camera feed
* Better user interaction

---

# Application Architecture

```
Barcode Reader Application
│
├── barcode_main.py
│   ├── GUI (Flet)
│   ├── Camera capture (OpenCV)
│   ├── Barcode decoding (ZXing)
│   ├── Navigation & UI routing
│   ├── Reusable component functions
│   ├── Live search and filter logic
│   ├── Expiry tracking and colour logic
│   └── User interaction logic
│
├── database.py
│   ├── SQLite database initialization
│   ├── Schema migration (non-destructive)
│   ├── Insert scanned barcodes
│   ├── Update labels
│   ├── Fetch scan history
│   └── Delete records
│
├── barcode_generator.py
│   └── Barcode regeneration using python-barcode
│
└── barcode_history.db
    └── Persistent local storage (excluded from version control)
```

---

# Technologies Used

| Technology      | Purpose                   |
| --------------- | ------------------------- |
| Python          | Core application language |
| OpenCV          | Webcam frame capture      |
| ZXing (pyzxing) | Barcode decoding          |
| python-barcode  | Barcode regeneration      |
| SQLite          | Local persistent storage  |
| Flet            | Desktop GUI framework     |
| Pillow          | Image processing          |
| Threading       | Background camera capture |

---

# Key Engineering Decisions

## Manual Capture Instead of Continuous Scanning

Continuous scanning produced **partial barcode reads**.

A manual **Capture button** ensures the user can properly frame the barcode before decoding.

---

## ZXing Instead of pyzbar

The initial implementation used **pyzbar**, but it struggled with **long ITF barcodes** commonly used in retail clothing tags.

ZXing provided:

* Higher detection reliability
* Support for longer barcodes
* Better scanning accuracy

---

## Reusable Component Architecture

Rather than repeating UI code across pages, shared elements like headers, buttons, and cards are encapsulated in **component functions**. This follows the DRY (Don't Repeat Yourself) principle and makes the UI easy to maintain and retheme.

---

## In-Memory Search Filtering

The search feature loads all items from the database **once** on page load and filters the in-memory list on each keystroke. This avoids unnecessary database queries and keeps the search response instant.

---

## Runtime Expiry Calculation

Days remaining are calculated fresh on every page load using the stored `scan_time` and `return_window` values. This avoids storing a value that would become stale between sessions.

---

## Non-Destructive Database Migration

When new columns are added to the schema, the application checks whether the column already exists before running `ALTER TABLE`. This preserves all existing data while extending the schema safely.

---

## Library Format Mapping

ZXing and python-barcode use **different barcode naming formats**.

A **translation layer** was implemented to bridge this difference.

---

# Running the Application

## Clone the repository

```bash
git clone https://github.com/VishPetkar13/BarCode_Reader.git
cd BarCode_Reader
```

## Create and activate a virtual environment

```bash
python -m venv barenv
barenv\Scripts\activate  # Windows
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Run the application

```bash
python barcode_main.py
```

---

# Future Improvements

Planned enhancements include:

* Edit existing barcode labels
* Custom return window per barcode set at scan time
* Expiry notifications via desktop alerts
* Settings page with theme and font customisation
* Export barcode images
* Automatic cleanup of expired barcodes
* Mobile deployment (Android / iOS via Flet mobile builds)
* Performance optimisations for the scanning pipeline

---

# Example Use Case

1. Purchase clothing from a retail store
2. Scan the barcode from the receipt or clothing tag
3. Label the barcode *(e.g., Blue Hoodie)*
4. Store it in the application
5. Check the history page to see how many days remain in the return window
6. Search for it by name when returning the item
7. Delete it once the return window has expired

---

# Learning Outcomes

This project demonstrates hands-on experience with:

* Computer vision and barcode decoding
* Desktop GUI application development
* SQLite database design and schema migration
* Multi-threaded programming
* Reusable UI component architecture
* Real-time search and filter implementation
* Expiry tracking with runtime calculation
* Semantic colour systems for status indicators
* Cross-library integration and compatibility handling
* Git version control with a structured branching workflow

---

# Author

**Vishal Petkar**

MSc Data Analytics graduate interested in data engineering, Python development, machine learning, and building practical data-driven applications.

---

## License

This project is licensed under the MIT License.

For commercial use, collaboration, or custom development inquiries, please contact the author.