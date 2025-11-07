import cv2
import numpy as np
import sys
from masks import rMagenta, rRed, rGreen, rBlue, rOrange, rBlack

# 顏色變數與名稱
color_names = ["Magenta", "Red", "Green", "Blue", "Orange", "Black"]
mask_vars = [rMagenta, rRed, rGreen, rBlue, rOrange, rBlack]

# 初始滑桿值
low_L, high_L = 0, 255
low_A, high_A = 0, 255
low_B, high_B = 0, 255

# 滑桿回調函數
def on_low_L(val):  global low_L; low_L = min(val, high_L - 1)
def on_high_L(val): global high_L; high_L = max(val, low_L + 1)
def on_low_A(val):  global low_A; low_A = min(val, high_A - 1)
def on_high_A(val): global high_A; high_A = max(val, low_A + 1)
def on_low_B(val):  global low_B; low_B = min(val, high_B - 1)
def on_high_B(val): global high_B; high_B = max(val, low_B + 1)

# 建立影像視窗與滑桿
cv2.namedWindow("Color Picker")
cv2.createTrackbar("Low L", "Color Picker", low_L, 255, on_low_L)
cv2.createTrackbar("High L", "Color Picker", high_L, 255, on_high_L)
cv2.createTrackbar("Low A", "Color Picker", low_A, 255, on_low_A)
cv2.createTrackbar("High A", "Color Picker", high_A, 255, on_high_A)
cv2.createTrackbar("Low B", "Color Picker", low_B, 255, on_low_B)
cv2.createTrackbar("High B", "Color Picker", high_B, 255, on_high_B)

# GStreamer 相機管線（Orin Nano）
def gstreamer_pipeline(capture_width=640, capture_height=480,
                       display_width=640, display_height=480,
                       framerate=30, flip_method=0):
    return (
        "nvarguscamerasrc ! "
        f"video/x-raw(memory:NVMM), width={capture_width}, height={capture_height}, "
        f"format=NV12, framerate={framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width={display_width}, height={display_height}, format=BGRx ! "
        "videoconvert ! video/x-raw, format=BGR ! appsink"
    )

cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
if not cap.isOpened():
    print("❌ 無法開啟相機")
    sys.exit(1)

# 建立按鈕視窗
cv2.namedWindow("Buttons")
buttons_img = np.zeros((500, 600, 3), np.uint8)
button_size = (250, 80)

buttons = {
    'Magenta': (20, 100),
    'Red': (20, 220),
    'Green': (20, 340),
    'Blue': (300, 100),
    'Orange': (300, 220),
    'Black': (300, 340),
    'Reset': (300, 460),
    'Save & Quit': (20, 460)
}

# 畫按鈕
for text, pos in buttons.items():
    color = (255, 255, 255)
    if text in color_names:
        color = (0, 255, 0)
    elif text in ["Reset"]:
        color = (255, 200, 0)
    elif text in ["Save & Quit"]:
        color = (0, 0, 255)

    cv2.rectangle(buttons_img,
                  (pos[0], pos[1] - button_size[1]),
                  (pos[0] + button_size[0], pos[1]),
                  color, -1)
    cv2.putText(buttons_img, text, (pos[0] + 10, pos[1] - 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

# 儲存到 masks.py
def save_masks():
    with open("masks.py", "w") as f:
        f.write(f"rMagenta = {mask_vars[0]}\n")
        f.write(f"rRed = {mask_vars[1]}\n")
        f.write(f"rGreen = {mask_vars[2]}\n")
        f.write(f"rBlue = {mask_vars[3]}\n")
        f.write(f"rOrange = {mask_vars[4]}\n")
        f.write(f"rBlack = {mask_vars[5]}\n")
    print("💾 已儲存所有顏色到 masks.py")

# 滑鼠點擊事件
def mouse_callback(event, x, y, flags, param):
    global low_L, high_L, low_A, high_A, low_B, high_B
    if event == cv2.EVENT_LBUTTONDOWN:
        for idx, (text, pos) in enumerate(buttons.items()):
            x1, y1 = pos[0], pos[1] - button_size[1]
            x2, y2 = pos[0] + button_size[0], pos[1]
            if x1 <= x <= x2 and y1 <= y <= y2:
                if text in color_names:
                    index = color_names.index(text)
                    mask_vars[index][0] = [low_L, low_A, low_B]
                    mask_vars[index][1] = [high_L, high_A, high_B]
                    print(f"💾 已儲存 {text} 顏色")
                elif text == "Reset":
                    low_L, high_L = 0, 255
                    low_A, high_A = 0, 255
                    low_B, high_B = 0, 255
                    cv2.setTrackbarPos("Low L", "Color Picker", low_L)
                    cv2.setTrackbarPos("High L", "Color Picker", high_L)
                    cv2.setTrackbarPos("Low A", "Color Picker", low_A)
                    cv2.setTrackbarPos("High A", "Color Picker", high_A)
                    cv2.setTrackbarPos("Low B", "Color Picker", low_B)
                    cv2.setTrackbarPos("High B", "Color Picker", high_B)
                    print("🔄 已重設滑桿")
                elif text == "Save & Quit":
                    save_masks()
                    cap.release()
                    cv2.destroyAllWindows()
                    sys.exit(0)

cv2.setMouseCallback("Buttons", mouse_callback)

# 主迴圈
while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ 讀取影像失敗")
        break

    # 顏色篩選
    lab_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
    mask = cv2.inRange(lab_frame, (low_L, low_A, low_B), (high_L, high_A, high_B))
    result = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("Color Picker", result)
    cv2.imshow("Buttons", buttons_img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
