// ─────────────────────────────────────────────
//  STORAGE  (replaces database.py)
// ─────────────────────────────────────────────

function getAllItems() {
  const data = localStorage.getItem("barcodeItems");
  return data ? JSON.parse(data) : [];
}

function saveItem(barcode_value, barcode_type, user_label) {
  const items = getAllItems();

  // Mirror the UNIQUE constraint from the old SQLite schema
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

  // Best-effort attempt at continuous autofocus.
  // Not supported on all browsers/devices, so we ignore failures silently.
  const track = stream.getVideoTracks()[0];
  track.applyConstraints({ advanced: [{ focusMode: "continuous" }] }).catch(() => {});
}).catch(err => {
  resultText.innerText = "Camera error: " + err;
});

function captureFrame() {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);

  return new Promise(resolve => {
    canvas.toBlob(blob => {
      resolve(new File([blob], "capture.jpg", { type: "image/jpeg" }));
    }, "image/jpeg", 1.0);
  });
}

async function tryDecode(attemptsRemaining) {
  const file = await captureFrame();

  try {
    const decodedText = await html5QrCode.scanFile(file, false);
    detectedValue.innerText = decodedText;
    confirmArea.style.display = "block";
    resultText.innerText = "Barcode detected";
  } catch (err) {
    if (attemptsRemaining > 1) {
      resultText.innerText = "Still trying... (" + attemptsRemaining + " attempts left)";
      setTimeout(() => tryDecode(attemptsRemaining - 1), 300);
    } else {
      resultText.innerText = "No barcode detected, try again";
    }
  }
}

document.getElementById("captureBtn").addEventListener("click", () => {
  resultText.innerText = "Capturing...";
  // Small delay lets autofocus settle after the tap before the first attempt
  setTimeout(() => tryDecode(3), 400);
});

document.getElementById("confirmYes").addEventListener("click", () => {
  const value = detectedValue.innerText;
  const label = document.getElementById("labelInput").value;

  // We don't know the exact format from a captured image the same way
  // ZXing did on desktop, so we store it generically for now.
  const saved = saveItem(value, "UNKNOWN", label);

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