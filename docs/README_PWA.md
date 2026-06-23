# Barcode Vault — Progressive Web App (PWA)

![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow)
![Flask](https://img.shields.io/badge/Backend-Flask-black)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![PWA](https://img.shields.io/badge/Platform-Progressive%20Web%20App-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

A **mobile-first, installable web application** for scanning, storing, and managing retail return barcodes — built as a cross-platform companion to the original Python/Flet desktop application, using a hybrid client/cloud architecture to overcome native mobile packaging limitations.

The application allows users to:

* Scan retail barcodes using their phone's camera
* Decode barcodes via a cloud-hosted native decoding service
* Store scan history locally on their own device
* Label, search, and track return windows for saved barcodes
* View and regenerate barcode images
* Delete barcodes once no longer needed

---

## Recruiter / Portfolio Summary

This project demonstrates the ability to recognise a genuine platform limitation, evaluate multiple technical alternatives, and execute a deliberate architectural pivot under real time constraints — skills directly relevant to **software engineering, systems design, and pragmatic problem-solving** in production environments.

### Key Competencies Demonstrated

* Progressive Web App (PWA) development
* Browser camera API integration (`getUserMedia`, `Canvas`)
* Client-side persistent storage (`localStorage`) as a lightweight database substitute
* RESTful API design and implementation (Flask)
* Cross-Origin Resource Sharing (CORS) configuration
* Cloud deployment and hosting (PythonAnywhere)
* Native barcode decoding via `zxing-cpp`
* Responsive, theme-driven UI design using CSS custom properties
* Architectural decision-making and platform constraint evaluation
* Git branching workflow across a multi-platform project

### Engineering Highlights

* Diagnosed and documented a genuine **Android packaging limitation** preventing native barcode decoding libraries from being bundled into a Flet/Flutter mobile build, and made a deliberate decision to pivot rather than force an unworkable approach.
* Designed and built a **hybrid client/cloud architecture**: barcode images are captured client-side and decoded server-side using a native, desktop-grade decoding library, combining the convenience of a web app with the reliability of native software.
* Implemented a **fully local, privacy-conscious storage model** — barcode data never leaves the user's device persistently; only a transient image is sent to the decoding service per scan, with no logging or retention server-side.
* Built a **custom scan reticle UI** that crops the captured image to the targeted region before processing, improving decode accuracy and reducing irrelevant background interference.
* Designed a **cohesive visual identity system** using CSS custom properties (design tokens), allowing the entire colour palette to be defined and adjusted from a single source of truth.

---

## Why a PWA Instead of a Native Android App?

The original goal was to port the desktop application directly to Android using Flet's Flutter-based build system. During development, this approach hit a structural wall:

* The original decoding library (`pyzxing`) requires a Java runtime, unavailable on Android.
* Alternative libraries (`zxing-cpp`, `pyrxing`) had no pre-built Android-compatible binaries available through Flet's mobile packaging system, and attempts to compile them from source during the build process failed due to toolchain restrictions specific to cross-compilation for Android.
* This was confirmed to be a genuine ecosystem limitation, not a fixable configuration issue, after thorough investigation including direct testing of source-based builds.

Rather than abandon mobile support or invest significant time learning native Android/Kotlin development under time constraints, a **Progressive Web App** was identified as a pragmatic alternative: browsers already provide mature camera access APIs, requiring no platform-specific build pipeline at all.

---

## Why a Cloud Decoding Server?

Initial PWA scanning used a JavaScript barcode-decoding library (`html5-qrcode`) running directly in the browser. While functional, this approach proved noticeably less reliable than the original desktop application — particularly with longer 1D barcode formats (ITF) used on certain retail receipts.

To close this reliability gap without abandoning the web-based approach, the architecture was extended:

* A small Flask application was deployed to a free hosting service (PythonAnywhere).
* This server uses **`zxing-cpp`**, the same calibre of native decoding library used in the original desktop application, which installs cleanly on a standard Linux server with pre-built binaries (unlike the Android packaging environment).
* The PWA now captures an image client-side and sends it to this server for decoding, receiving back only the decoded text value.
* This achieves **native-grade decoding reliability** while keeping the application installable, cross-platform, and free to run.

---

## Features

### Barcode Scanning

* Camera access via the browser's `getUserMedia` API
* Manual capture (rather than continuous scanning), consistent with the original desktop application's design philosophy of avoiding partial reads
* A scan reticle (styled corner brackets) indicating the targeted capture region
* Captured image is cropped to the targeted region before being sent for decoding, reducing background interference

### Cloud-Based Decoding

* Flask backend hosted on PythonAnywhere
* `/decode` endpoint accepts an image and returns the decoded barcode value and format
* Powered by `zxing-cpp`, supporting ITF, Code 128, Code 39, EAN-13, EAN-8, UPC-A, and UPC-E
* No image or barcode data is logged or retained server-side

### Local Persistent Storage

All scanned barcodes are stored in the browser's `localStorage`, structured as a JSON array of records:

| Field | Description |
| --- | --- |
| barcode_value | Raw barcode data |
| barcode_type | Decoded barcode format |
| user_label | User-defined label |
| scan_time | ISO timestamp of scan |
| return_window | Return window in days (default: 28) |

Duplicate barcode values are ignored on save, mirroring the original application's database-level uniqueness constraint.

### Labeling System

Users are prompted to name a barcode immediately after a successful scan, with the option to edit the label later from the barcode detail view.

### Search and Filter

A live search bar filters saved barcodes by label or barcode value as the user types.

### Expiry Tracking

Each barcode's days remaining in its return window is calculated at runtime and displayed with a colour-coded status:

| Status | Colour | Condition |
| --- | --- | --- |
| Safe | Green | More than 8 days remaining |
| Warning | Gold | 4 to 8 days remaining |
| Expired / Critical | Red | 0 to 3 days remaining |

### Barcode Viewer

Selecting a saved barcode opens a detail view showing a regenerated barcode image (via the JsBarcode library), the raw value, format, scan date, and expiry status, with options to edit the label or delete the entry.

### Delete Functionality

Barcodes can be permanently removed with a confirmation prompt.

### About / Privacy Disclosure

A dedicated page explains the application's data handling: all barcode data is stored locally on the user's device only, with an explicit warning that clearing browser site data will permanently delete saved history with no recovery option.

---

## Application Architecture

```
Barcode Vault PWA
│
├── docs/index.html
│   ├── Page structure and layout (Scanner, History, Detail, About views)
│   └── Visual design system (CSS custom properties)
│
├── docs/app.js
│   ├── Camera access and capture logic
│   ├── Cloud decoding integration (fetch to Flask backend)
│   ├── localStorage data layer (save, update, delete, retrieve)
│   ├── Expiry calculation and colour coding
│   ├── Search/filter logic
│   ├── Barcode image regeneration (JsBarcode)
│   └── View navigation (show/hide section routing)
│
└── Flask backend (hosted on PythonAnywhere)
    ├── /decode endpoint
    ├── zxing-cpp native barcode decoding
    └── CORS configuration
```

---

## Technologies Used

| Technology | Purpose |
| --- | --- |
| HTML5 / CSS3 | Page structure and visual design |
| JavaScript (ES6) | Application logic, camera handling, storage |
| `getUserMedia` API | Browser camera access |
| `localStorage` | Client-side persistent storage |
| Flask | Backend web framework |
| `zxing-cpp` | Native barcode decoding |
| `flask-cors` | Cross-origin request handling |
| JsBarcode | Client-side barcode image generation |
| GitHub Pages | Static site hosting |
| PythonAnywhere | Backend server hosting |

---

## Key Engineering Decisions

### Manual Capture Over Continuous Scanning

Consistent with the original desktop application, the PWA uses a deliberate capture action rather than continuous live decoding, avoiding partial or unstable reads.

### Scan Region Cropping

Rather than sending the entire camera frame for decoding, the captured image is cropped to the visible scan reticle region client-side. This reduces irrelevant background content (such as surrounding receipt text) reaching the decoder.

### Hybrid Client/Cloud Decoding

Decoding logic was deliberately moved server-side once browser-based decoding proved insufficiently reliable for certain barcode formats, while all persistent user data remains entirely client-side. This separation keeps the architecture privacy-conscious while solving a genuine reliability problem.

### Format Mapping for Barcode Regeneration

Barcode format identifiers returned by the decoding service are mapped to the naming conventions expected by the client-side rendering library, mirroring the equivalent format-translation layer in the original desktop application.

### Defensive Rendering

Barcode image regeneration is wrapped in error handling, falling back to a text-only display if a given format cannot be rendered, rather than allowing a rendering failure to break the page.

---

## Running the Application

This application is hosted and does not require local installation to use. To run a local copy for development:

```bash
git clone https://github.com/VishPetkar13/BarCode_Reader.git
cd BarCode_Reader/docs
python -m http.server 8000
```

Then open `http://localhost:8000` in a browser. Camera access requires a secure context (`localhost` or HTTPS), which both local development servers and GitHub Pages satisfy.

---

## Future Improvements

* User-selectable visual themes
* Editable return window per barcode at scan time
* Expiry notifications
* Custom branded visual identity
* Minification of client-side assets

---

## Author

**Vishal Petkar**

MSc Data Analytics graduate interested in data engineering, Python development, machine learning, and building practical, cross-platform data-driven applications.

---

## License

This project is licensed under the MIT License.