# BarCode_Reader
This project to to create a barcode reader that reads barcode and stores it in persistantly in a local database

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
* Store them locally in a database
* Label them for future reference
* Retrieve them when returning items
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
* SQLite database design and persistence
* Multi-threaded programming
* Data storage and retrieval workflows
* Cross-library integration and compatibility handling
* UX-focused feature design

### Engineering Highlights

* Implemented **real-time barcode scanning** via webcam using OpenCV.
* Integrated **ZXing barcode detection** to improve accuracy over alternative libraries.
* Designed a **SQLite database schema** for persistent barcode storage.
* Built an **interactive GUI desktop application** using Flet.
* Implemented **threaded camera processing** to prevent UI blocking.
* Created a **format translation layer** to resolve compatibility differences between barcode libraries.
* Developed **barcode regeneration functionality** using python-barcode.

---

# Project Motivation

Retail stores often print **return barcodes on receipts or clothing tags** that are required for refunds or exchanges within a limited period (commonly **28 days**).

These barcodes are easy to **lose or damage**.

This application provides a digital solution where users can:

* Scan and store return barcodes
* Label them for easy identification
* View them later when returning items
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

| Field         | Description                |
| ------------- | -------------------------- |
| id            | Auto-increment primary key |
| barcode_value | Raw barcode data           |
| barcode_type  | Barcode format             |
| user_label    | User-defined label         |
| scan_time     | Timestamp of scan          |

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

* Item Label
* Scan Timestamp

History is automatically **sorted by most recent scans first**.

Users can **click any item** to view the stored barcode.

---

## Barcode Viewer

Selecting a saved item opens a screen displaying the **reconstructed barcode**.

From this screen users can:

* Go back to history
* Delete the barcode

---

## Delete Functionality

Users can remove stored barcodes when they are **no longer needed**.

Example use case:

A store’s **return window has expired** and the barcode is no longer required.

The delete feature includes:

* Confirmation dialog
* Immediate database removal
* Automatic history refresh
* Snackbar notification for user feedback

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
│   └── User interaction logic
│
├── database.py
│   ├── SQLite database initialization
│   ├── Insert scanned barcodes
│   ├── Update labels
│   ├── Fetch scan history
│   └── Delete records
│
├── barcode_generator.py
│   └── Barcode regeneration using python-barcode
│
└── barcode_history.db
    └── Persistent local storage
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

## Library Format Mapping

ZXing and python-barcode use **different barcode naming formats**.

A **translation layer** was implemented to bridge this difference.

---

# Running the Application

## Clone the repository

```bash
git clone https://github.com/yourusername/barcode-reader.git
cd barcode-reader
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

* Search functionality for scan history
* Edit existing barcode labels
* Export barcode images
* Automatic cleanup of expired barcodes
* Mobile deployment (Android / iOS)
* UI styling improvements
* Performance optimizations for scanning

---

# Example Use Case

1. Purchase clothing from a retail store
2. Scan the barcode from the receipt or clothing tag
3. Label the barcode *(e.g., Blue Hoodie)*
4. Store it in the application
5. Retrieve the barcode later when returning the item

---

# Learning Outcomes

This project demonstrates experience with:

* Computer vision
* Barcode decoding
* Desktop GUI application development
* SQLite database design
* Multi-threaded programming
* Cross-library integration
* UX-focused feature design

---

# Author

**Vishal Petkar**

MSc Data Analytics graduate interested in:

* Data engineering
* Python development
* Machine learning
* Building practical data-driven applications

## License

This project is licensed under the MIT License.

For commercial use, collaboration, or custom development inquiries, 
please contact the author.
