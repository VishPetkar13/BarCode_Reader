// ─────────────────────────────────────────────
//  STORAGE  (replaces database.py)
// ─────────────────────────────────────────────

function getAllItems() {
  const data = localStorage.getItem("barcodeItems");
  return data ? JSON.parse(data) : [];
}

function saveAllItems(items) {
  localStorage.setItem("barcodeItems", JSON.stringify(items));
}

function saveItem(barcode_value, barcode_type, user_label) {
  const items = getAllItems();

  const alreadyExists = items.some(item => item.barcode_value === barcode_value);
  if (alreadyExists) {
    return false;
  }

  const newItem = {
    barcode_value: barcode_value,
    barcode_type: barcode_type,
    user_label: user_label || null,
    scan_time: new Date().toISOString(),
    return_window: 28
  };

  items.push(newItem);
  saveAllItems(items);
  return true;
}

function updateLabel(barcode_value, newLabel) {
  const items = getAllItems();
  const item = items.find(i => i.barcode_value === barcode_value);
  if (item) {
    item.user_label = newLabel || null;
    saveAllItems(items);
  }
}

function deleteItem(barcode_value) {
  const items = getAllItems();
  const filtered = items.filter(i => i.barcode_value !== barcode_value);
  saveAllItems(filtered);
}

// ─────────────────────────────────────────────
//  EXPIRY TRACKING  (mirrors days_remaining / expiry_color from desktop app)
//  Green:  more than 8 days remaining
//  Yellow: 4 to 8 days remaining
//  Red:    0 to 3 days remaining
// ─────────────────────────────────────────────

function daysRemaining(scanTimeISO, returnWindow) {
  const scanDate = new Date(scanTimeISO);
  const today = new Date();
  const msPerDay = 1000 * 60 * 60 * 24;
  const daysPassed = Math.floor((today - scanDate) / msPerDay);
  const remaining = returnWindow - daysPassed;
  return remaining > 0 ? remaining : 0;
}

function expiryColor(days) {
  if (days > 8) return "var(--accent-green)";
  if (days >= 4) return "var(--accent-gold)";
  return "var(--danger)";
}

// ─────────────────────────────────────────────
//  CAMERA + CAPTURE  (replaces camera section of barcode_main.py)
// ─────────────────────────────────────────────

const video = document.getElementById("preview");
const canvas = document.getElementById("snapshot");
const resultText = document.getElementById("result");
const confirmArea = document.getElementById("confirmArea");
const detectedValue = document.getElementById("detectedValue");

let lastDetectedFormat = "UNKNOWN";

navigator.mediaDevices.getUserMedia({
  video: { facingMode: "environment" }
}).then(stream => {
  video.srcObject = stream;
}).catch(err => {
  resultText.innerText = "Camera error: " + err;
});

document.getElementById("captureBtn").addEventListener("click", () => {
  resultText.innerText = "Capturing...";

  const scanBox = document.getElementById("scanBox");
  const videoRect = video.getBoundingClientRect();
  const boxRect = scanBox.getBoundingClientRect();

  const scaleX = video.videoWidth / videoRect.width;
  const scaleY = video.videoHeight / videoRect.height;

  const sx = (boxRect.left - videoRect.left) * scaleX;
  const sy = (boxRect.top - videoRect.top) * scaleY;
  const sWidth = boxRect.width * scaleX;
  const sHeight = boxRect.height * scaleY;

  canvas.width = sWidth;
  canvas.height = sHeight;
  canvas.getContext("2d").drawImage(video, sx, sy, sWidth, sHeight, 0, 0, sWidth, sHeight);

  canvas.toBlob(blob => {
    const formData = new FormData();
    formData.append("image", blob, "capture.jpg");

    resultText.innerText = "Sending to decoder...";

    fetch("https://barcodereader.eu.pythonanywhere.com/decode", {
      method: "POST",
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        if (data.value) {
          detectedValue.innerText = data.value;
          lastDetectedFormat = data.format || "UNKNOWN";
          confirmArea.style.display = "block";
          resultText.innerText = "Barcode detected";
        } else {
          resultText.innerText = "No barcode detected, try again";
        }
      })
      .catch(err => {
        resultText.innerText = "Server error: " + err;
      });
  }, "image/jpeg");
});

document.getElementById("confirmYes").addEventListener("click", () => {
  const value = detectedValue.innerText;
  const label = document.getElementById("labelInput").value;

  const saved = saveItem(value, lastDetectedFormat, label);

  if (saved) {
    resultText.innerText = "Saved as: " + (label || value);
  } else {
    resultText.innerText = "Already saved previously: " + value;
  }

  document.getElementById("labelInput").value = "";
  confirmArea.style.display = "none";
});

document.getElementById("confirmRetry").addEventListener("click", () => {
  confirmArea.style.display = "none";
  resultText.innerText = "Try capturing again";
});

// ─────────────────────────────────────────────
//  HISTORY PAGE  (replaces history route in barcode_main.py)
// ─────────────────────────────────────────────

function renderHistory(searchTerm) {
  let items = getAllItems();

  if (searchTerm) {
    const term = searchTerm.toLowerCase();
    items = items.filter(item => {
      const label = (item.user_label || "").toLowerCase();
      const value = item.barcode_value.toLowerCase();
      return label.includes(term) || value.includes(term);
    });
  }

  const historyList = document.getElementById("historyList");

  if (items.length === 0) {
    historyList.innerHTML = "<p>No barcodes saved yet</p>";
    return;
  }

  historyList.innerHTML = items.map(item => {
    const display = item.user_label || item.barcode_value;
    const scanTime = new Date(item.scan_time).toLocaleString();
    const remaining = daysRemaining(item.scan_time, item.return_window);
    const color = expiryColor(remaining);
    const statusText = remaining > 0 ? remaining + " days remaining" : "Expired";

    return `
      <div class="historyCard" data-value="${item.barcode_value}">
        <strong>${display}</strong><br>
        <span>${scanTime}</span><br>
        <span style="color: ${color}; font-weight: 600;">${statusText}</span>
      </div>
    `;
  }).join("");

  document.querySelectorAll(".historyCard").forEach(card => {
    card.addEventListener("click", () => {
      openItemView(card.getAttribute("data-value"));
    });
  });
}

document.getElementById("searchInput").addEventListener("input", (e) => {
  renderHistory(e.target.value);
});

// ─────────────────────────────────────────────
//  BARCODE VIEWER  (replaces barcode_generator.py + viewer route)
// ─────────────────────────────────────────────

const formatMap = {
  "EAN-13": "EAN13",
  "EAN-8": "EAN8",
  "UPC-A": "UPC",
  "UPC-E": "UPCE",
  "Code128": "CODE128",
  "ITF": "ITF"
};

let currentViewedValue = null;

function openItemView(barcodeValue) {
  const items = getAllItems();
  const item = items.find(i => i.barcode_value === barcodeValue);
  if (!item) return;

  currentViewedValue = barcodeValue;

  document.getElementById("viewValue").innerText = item.barcode_value;
  document.getElementById("viewType").innerText = item.barcode_type;
  document.getElementById("viewScanTime").innerText = new Date(item.scan_time).toLocaleString();
  document.getElementById("editLabelInput").value = item.user_label || "";

  const remaining = daysRemaining(item.scan_time, item.return_window);
  const color = expiryColor(remaining);
  const statusEl = document.getElementById("viewExpiryStatus");
  statusEl.innerText = remaining > 0 ? remaining + " days remaining" : "Expired";
  statusEl.style.color = color;
  statusEl.style.fontWeight = "600";

  const svg = document.getElementById("barcodeSvg");
  const fallback = document.getElementById("barcodeRenderFallback");
  svg.style.display = "block";
  fallback.style.display = "none";

  try {
    const jsBarcodeFormat = formatMap[item.barcode_type] || "CODE128";
    JsBarcode(svg, item.barcode_value, { format: jsBarcodeFormat });
  } catch (err) {
    svg.style.display = "none";
    fallback.style.display = "block";
  }

  document.getElementById("historyView").style.display = "none";
  document.getElementById("viewItemView").style.display = "block";
}

document.getElementById("saveLabelBtn").addEventListener("click", () => {
  const newLabel = document.getElementById("editLabelInput").value;
  updateLabel(currentViewedValue, newLabel);
  alert("Label saved");
});

document.getElementById("deleteItemBtn").addEventListener("click", () => {
  const confirmed = confirm("Delete this barcode? This cannot be undone.");
  if (confirmed) {
    deleteItem(currentViewedValue);
    document.getElementById("viewItemView").style.display = "none";
    document.getElementById("historyView").style.display = "block";
    renderHistory();
  }
});

document.getElementById("backFromViewBtn").addEventListener("click", () => {
  document.getElementById("viewItemView").style.display = "none";
  document.getElementById("historyView").style.display = "block";
  renderHistory();
});

// ─────────────────────────────────────────────
//  NAVIGATION  (replaces page.go() routing in barcode_main.py)
// ─────────────────────────────────────────────

document.getElementById("viewHistoryBtn").addEventListener("click", () => {
  document.getElementById("scannerView").style.display = "none";
  document.getElementById("historyView").style.display = "block";
  document.getElementById("searchInput").value = "";
  renderHistory();
});

document.getElementById("backToScannerBtn").addEventListener("click", () => {
  document.getElementById("historyView").style.display = "none";
  document.getElementById("scannerView").style.display = "block";
});

document.getElementById("viewAboutBtn").addEventListener("click", () => {
  document.getElementById("scannerView").style.display = "none";
  document.getElementById("aboutView").style.display = "block";
});

document.getElementById("backFromAboutBtn").addEventListener("click", () => {
  document.getElementById("aboutView").style.display = "none";
  document.getElementById("scannerView").style.display = "block";
});