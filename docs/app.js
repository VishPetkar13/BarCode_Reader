// ─────────────────────────────────────────────
//  STORAGE  (replaces database.py)
// ─────────────────────────────────────────────

function getAllItems() {
  const data = localStorage.getItem("barcodeItems");
  return data ? JSON.parse(data) : [];
}

function saveItem(barcode_value, barcode_type) {
  const items = getAllItems();

  // Mirror the UNIQUE constraint from the old SQLite schema
  const alreadyExists = items.some(item => item.barcode_value === barcode_value);
  if (alreadyExists) {
    return false;
  }

  const newItem = {
    barcode_value: barcode_value,
    barcode_type: barcode_type,
    user_label: null,
    scan_time: new Date().toISOString(),
    return_window: 28
  };

  items.push(newItem);
  localStorage.setItem("barcodeItems", JSON.stringify(items));
  return true;
}

// ─────────────────────────────────────────────
//  CAMERA + CAPTURE  (replaces camera section of barcode_main.py)
// ─────────────────────────────────────────────

const video = document.getElementById("preview");
const canvas = document.getElementById("snapshot");
const resultText = document.getElementById("result");
const confirmArea = document.getElementById("confirmArea");
const detectedValue = document.getElementById("detectedValue");

const html5QrCode = new Html5Qrcode("snapshot");

// Start the live camera preview (simple, single preference, no extras)
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

  // We don't know the exact format from a captured image the same way
  // ZXing did on desktop, so we store it generically for now.
  const saved = saveItem(value, "UNKNOWN");

  if (saved) {
    resultText.innerText = "Saved: " + value;
  } else {
    resultText.innerText = "Already saved previously: " + value;
  }

  confirmArea.style.display = "none";
});

document.getElementById("confirmRetry").addEventListener("click", () => {
  confirmArea.style.display = "none";
  resultText.innerText = "Try capturing again";
});