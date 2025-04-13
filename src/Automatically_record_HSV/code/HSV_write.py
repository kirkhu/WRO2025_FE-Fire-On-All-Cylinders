import cv2 
import numpy as np 
import pickle

def nothing(x):
    pass

img2 = np.zeros((300, 512, 3), np.uint8)
cv2.namedWindow('image')

# Create trackbars for color change
cv2.createTrackbar('H_low', 'image', 0, 255, nothing)
cv2.createTrackbar('H_high', 'image', 255, 255, nothing)
cv2.createTrackbar('S_low', 'image', 0, 255, nothing)
cv2.createTrackbar('S_high', 'image', 255, 255, nothing)
cv2.createTrackbar('V_low', 'image', 0, 255, nothing)
cv2.createTrackbar('V_high', 'image', 255, 255, nothing)

# Camera setup
imcap = cv2.VideoCapture('nvarguscamerasrc ! video/x-raw(memory:NVMM), width=640, height=480, format=(string)NV12, framerate=(fraction)30/1 ! nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink', cv2.CAP_GSTREAMER)

imcap.set(cv2.CAP_PROP_BRIGHTNESS, 60)
imcap.set(3, 480)  # set width as 640
imcap.set(4, 360)  # set height as 480
kernal = np.ones((5, 5))

# Dictionary to hold HSV values for different colors
hsv_values = {'Blue': None, 'Orange': None, 'Red': None, 'Green': None, 'Pink': None}

# Print available actions
def print_actions():
    print("\nKey Action Instructions:")
    print("Press '1' to save the current HSV values as Blue")
    print("Press '2' to save the current HSV values as Orange")
    print("Press '3' to save the current HSV values as Red")
    print("Press '4' to save the current HSV values as Green")
    print("Press '5' to save the current HSV values as Pink")
    print("Press 'q' to save all HSV values and exit the program\n")


# Initial print to show the available actions
print_actions()
i = 0
while True:
    H_high = cv2.getTrackbarPos('H_high', 'image')
    H_low = cv2.getTrackbarPos('H_low', 'image')
    S_high = cv2.getTrackbarPos('S_high', 'image')
    S_low = cv2.getTrackbarPos('S_low', 'image')
    V_high = cv2.getTrackbarPos('V_high', 'image')
    V_low = cv2.getTrackbarPos('V_low', 'image')
    success, img = imcap.read()

    if not success:
        break
    elif i == 0:
        print_actions()
        i = i+1

    hls = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hls_low = np.array([H_low, S_low, V_low])
    hls_high = np.array([H_high, S_high, V_high])

    mask = cv2.inRange(hls, hls_low, hls_high)
    mask = cv2.dilate(mask, kernal, iterations=1)
    res = cv2.bitwise_and(img, img, mask=mask)

    cv2.imshow('image', res)

    key = cv2.waitKey(30) & 0xFF

    if key == ord('1'):
        # Save current HSV values as Blue
        hsv_values['Blue'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("Blue HSV values saved:", hsv_values['Blue'])
        print_actions()  # Print actions again after saving
    elif key == ord('2'):
        # Save current HSV values as Orange
        hsv_values['Orange'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("Orange HSV values saved:", hsv_values['Orange'])
        print_actions()
    elif key == ord('3'):
        # Save current HSV values as Red
        hsv_values['Red'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("Red HSV values saved:", hsv_values['Red'])
        print_actions()
    elif key == ord('4'):
        # Save current HSV values as Green
        hsv_values['Green'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("Green HSV values saved:", hsv_values['Green'])
        print_actions()
    elif key == ord('5'):
        # Save current HSV values as Pink
        hsv_values['Pink'] = ([H_low, S_low, V_low], [H_high, S_high, V_high])
        print("Pink HSV values saved:", hsv_values['Pink'])
        print_actions()
    elif key == ord('q'):
        # Save all values to a file and exit
        with open('hsv_values.pkl', 'wb') as f:
            pickle.dump(hsv_values, f)
        print("HSV values saved to hsv_values.pkl")
        break

cv2.destroyAllWindows()
