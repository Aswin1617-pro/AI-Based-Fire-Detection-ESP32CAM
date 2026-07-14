import cv2
import numpy as np
import requests
from ultralytics import YOLO
import cvzone
import math

# Load your model - Use 'yolov8n.pt' if you want maximum speed
model = YOLO('fire.pt')
classnames = ['fire']

# Stream URL
url = "http://10.63.253.228:81/stream"

print("Connecting to ESP32-CAM stream...")
try:
    # stream=True is essential for MJPEG
    response = requests.get(url, stream=True, timeout=10)
except Exception as e:
    print(f"Could not connect: {e}")
    exit()

bytes_data = b""

for chunk in response.iter_content(chunk_size=1024):
    bytes_data += chunk
    a = bytes_data.find(b'\xff\xd8')  # Start of JPEG
    b = bytes_data.find(b'\xff\xd9')  # End of JPEG

    if a != -1 and b != -1:
        jpg = bytes_data[a:b + 2]
        bytes_data = bytes_data[b + 2:]

        # Decode the image
        img_np = np.frombuffer(jpg, dtype=np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        if frame is not None:
            # OPTIONAL: Resize frame to 640x480 for faster AI inference
            frame = cv2.resize(frame, (640, 480))

            # Run YOLO detection
            results = model(frame, stream=True, verbose=False)  # verbose=False keeps console clean

            for info in results:
                boxes = info.boxes
                for box in boxes:
                    conf = math.ceil(box.conf[0] * 100)
                    cls = int(box.cls[0])

                    if conf > 50:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        # Draw Box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                        # Draw Label
                        cvzone.putTextRect(frame, f'{classnames[cls]} {conf}%',
                                           [max(0, x1), max(35, y1 - 10)],
                                           scale=1, thickness=1, offset=3)

            # Show the live feed
            cv2.imshow('ESP32-CAM Detection', frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()