import cv2
from ultralytics import YOLO
import cvzone
import math
import requests  # Needed for Telegram API
import os
from datetime import datetime

# --- SETTINGS ---
model_path = r'C:\Users\HP\AppData\Roaming\JetBrains\PyCharm2025.3\extensions\fire.pt'
stream_url = "http://10.149.109.228:81/stream"

# --- TELEGRAM CONFIG ---
BOT_TOKEN = "8768568292:AAGw26s5R57IzBGJKT8g8aIpMIthHmbyX80"
CHAT_ID = "7811340334"
# Create a folder to save evidence photos
if not os.path.exists("alerts"):
    os.makedirs("alerts")

print("Loading YOLO model...")
model = YOLO(model_path)


def send_telegram_alert(frame, confidence):
    """Saves the frame and sends it to Telegram"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = f"alerts/fire_{timestamp}.jpg"
    cv2.imwrite(file_path, frame)  # Save the image locally

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    caption = f"⚠️ FIRE DETECTED! \nConfidence: {confidence}% \nTime: {timestamp}"

    try:
        with open(file_path, 'rb') as photo:
            requests.post(url, data={'chat_id': CHAT_ID, 'caption': caption}, files={'photo': photo}, timeout=5)
        print("Telegram alert sent successfully!")
    except Exception as e:
        print(f"Failed to send Telegram: {e}")


# Initialize the capture
cap = cv2.VideoCapture(stream_url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

alert_counter = 0  # To prevent spamming messages

while True:
    success, frame = cap.read()
    if not success:
        print("Failed to grab frame. Retrying...")
        continue

    # Resizing for a better professional view
    frame = cv2.resize(frame, (1024, 768))

    # Run YOLO Detection
    results = model(frame, stream=True, verbose=False)

    for info in results:
        for box in info.boxes:
            conf = math.ceil(box.conf[0] * 100)
            if conf > 50:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cvzone.putTextRect(frame, f'FIRE {conf}%', [max(0, x1), max(35, y1 - 10)],
                                   scale=1, thickness=1, colorR=(0, 0, 255))

                # --- TRIGGER TELEGRAM ---
                if alert_counter == 0:
                    send_telegram_alert(frame, conf)
                    alert_counter = 50  # Wait for 50 frames before sending next alert

    # Countdown the alert timer
    if alert_counter > 0:
        alert_counter -= 1

    cv2.imshow('ESP32-CAM Fire Detection + Telegram', frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()