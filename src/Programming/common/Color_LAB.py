# Import the OpenCV library for computer vision tasks.
import cv2
# Import the NumPy library for numerical operations.
import numpy as np
# Import the sys library for system-level operations (like exiting).
import sys
# Import the predefined LAB color ranges from the 'masks.py' file.
from masks import rMagenta, rRed, rGreen, rBlue, rOrange, rBlack

# --- Color variables and names ---
# A list of strings for color names, used for UI and indexing.
color_names = ["Magenta", "Red", "Green", "Blue", "Orange", "Black"]
# A list holding the actual mask variables (imported from masks.py).
mask_vars = [rMagenta, rRed, rGreen, rBlue, rOrange, rBlack]

# --- Initial trackbar values ---
# Initialize the lower bound for the L (Lightness) channel.
low_L, high_L = 0, 255
# Initialize the lower bound for the A (Green-Red) channel.
low_A, high_A = 0, 255
# Initialize the lower bound for the B (Blue-Yellow) channel.
low_B, high_B = 0, 255

# --- Trackbar callback functions ---
# Callback function for the 'Low L' trackbar.
def on_low_L(val):  global low_L; low_L = min(val, high_L - 1)
# Callback function for the 'High L' trackbar.
def on_high_L(val): global high_L; high_L = max(val, low_L + 1)
# Callback function for the 'Low A' trackbar.
def on_low_A(val):  global low_A; low_A = min(val, high_A - 1)
# Callback function for the 'High A' trackbar.
def on_high_A(val): global high_A; high_A = max(val, low_A + 1)
# Callback function for the 'Low B' trackbar.
def on_low_B(val):  global low_B; low_B = min(val, high_B - 1)
# Callback function for the 'High B' trackbar.
def on_high_B(val): global high_B; high_B = max(val, low_B + 1)

# --- Create image window and trackbars ---
# Create the main window to display the masked image.
cv2.namedWindow("Color Picker")
# Create the 'Low L' trackbar and link it to its callback.
cv2.createTrackbar("Low L", "Color Picker", low_L, 255, on_low_L)
# Create the 'High L' trackbar and link it to its callback.
cv2.createTrackbar("High L", "Color Picker", high_L, 255, on_high_L)
# Create the 'Low A' trackbar and link it to its callback.
cv2.createTrackbar("Low A", "Color Picker", low_A, 255, on_low_A)
# Create the 'High A' trackbar and link it to its callback.
cv2.createTrackbar("High A", "Color Picker", high_A, 255, on_high_A)
# Create the 'Low B' trackbar and link it to its callback.
cv2.createTrackbar("Low B", "Color Picker", low_B, 255, on_low_B)
# Create the 'High B' trackbar and link it to its callback.
cv2.createTrackbar("High B", "Color Picker", high_B, 255, on_high_B)

# --- GStreamer Camera Pipeline ---
# Define a function to generate the GStreamer pipeline string...
def gstreamer_pipeline(capture_width=640, capture_height=480,
                       # ...for capturing from the Jetson's CSI camera.
                       display_width=640, display_height=480,
                       # (Function signature continues).
                       framerate=30, flip_method=0):
    # Return the formatted string.
    return (
        # NVIDIA camera source element.
        "nvarguscamerasrc ! "
        # Set camera properties (NVMM memory).
        f"video/x-raw(memory:NVMM), width={capture_width}, height={capture_height}, "
        # Set format and framerate.
        f"format=NV12, framerate={framerate}/1 ! "
        # NVIDIA video converter for flipping/conversion.
        f"nvvidconv flip-method={flip_method} ! "
        # Set output format to BGRx.
        f"video/x-raw, width={display_width}, height={display_height}, format=BGRx ! "
        # Software video converter.
        "videoconvert ! "
        # Final format BGR for OpenCV, sent to appsink.
        "video/x-raw, format=BGR ! appsink"
    )

# Initialize the video capture with the GStreamer pipeline.
cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
# Check if the camera failed to open.
if not cap.isOpened():
    # Print an error message.
    print("Cannot open camera")
    # Exit the script with an error code.
    sys.exit(1)

# --- Create Button Window ---
# Create a separate window to hold the control buttons.
cv2.namedWindow("Buttons")
# Create a black image to serve as the canvas for the buttons.
buttons_img = np.zeros((500, 600, 3), np.uint8)
# Define the standard size (width, height) for each button.
button_size = (250, 80)

# A dictionary mapping button text to their top-right (x, y) position.
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

# --- Draw Buttons ---
# Iterate through the dictionary of buttons.
for text, pos in buttons.items():
    # Set the default button color (white).
    color = (255, 255, 255)
    # If the button is a color name, make it green.
    if text in color_names:
        # Set color to green.
        color = (0, 255, 0)
    # If the button is 'Reset', make it blue.
    elif text in ["Reset"]:
        # Set color to blue.
        color = (255, 200, 0)
    # If the button is 'Save & Quit', make it red.
    elif text in ["Save & Quit"]:
        # Set color to red.
        color = (0, 0, 255)

    # Draw the button rectangle (filled).
    cv2.rectangle(buttons_img,
                  # Top-left corner (x, y - height).
                  (pos[0], pos[1] - button_size[1]),
                  # Bottom-right corner (x + width, y).
                  (pos[0] + button_size[0], pos[1]),
                  # Use the selected color, filled (-1).
                  color, -1)
    # Draw the button text.
    cv2.putText(buttons_img, text, (pos[0] + 10, pos[1] - 25),
                # Font settings.
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

# --- Save to masks.py ---
# Define the function to save the current mask values to 'masks.py'.
def save_masks():
    # Open 'masks.py' in write mode (overwrites existing file).
    with open("masks.py", "w") as f:
        # Write the line for rMagenta using the value from the list.
        f.write(f"rMagenta = {mask_vars[0]}\n")
        # Write the line for rRed.
        f.write(f"rRed = {mask_vars[1]}\n")
        # Write the line for rGreen.
        f.write(f"rGreen = {mask_vars[2]}\n")
        # Write the line for rBlue.
        f.write(f"rBlue = {mask_vars[3]}\n")
        # Write the line for rOrange.
        f.write(f"rOrange = {mask_vars[4]}\n")
        # Write the line for rBlack.
        f.write(f"rBlack = {mask_vars[5]}\n")
    # Print a confirmation message to the console.
    print("Masks saved to masks.py")

# --- Mouse Click Event ---
# Define the callback function for mouse events in the 'Buttons' window.
def mouse_callback(event, x, y, flags, param):
    # Access the global trackbar variables to modify them.
    global low_L, high_L, low_A, high_A, low_B, high_B
    # Check if the event is a left mouse button click.
    if event == cv2.EVENT_LBUTTONDOWN:
        # Iterate through all defined buttons.
        for idx, (text, pos) in enumerate(buttons.items()):
            # Calculate the button's bounding box.
            x1, y1 = pos[0], pos[1] - button_size[1]
            x2, y2 = pos[0] + button_size[0], pos[1]
            # Check if the click (x, y) is inside this button's box.
            if x1 <= x <= x2 and y1 <= y <= y2:
                # --- Clicked on a Color Button ---
                # If the button text is one of the color names:
                if text in color_names:
                    # Find the index of this color (0-5).
                    index = color_names.index(text)
                    # Update the lower bound in the list with current trackbar values.
                    mask_vars[index][0] = [low_L, low_A, low_B]
                    # Update the upper bound in the list.
                    mask_vars[index][1] = [high_L, high_A, high_B]
                    # Print confirmation.
                    print(f"Saved {text} values")
                # --- Clicked on the Reset Button ---
                # If the button text is 'Reset':
                elif text == "Reset":
                    # Reset the global trackbar variables to their defaults (0-255).
                    low_L, high_L = 0, 255
                    low_A, high_A = 0, 255
                    low_B, high_B = 0, 255
                    # Update the 'Low L' trackbar's visual position.
                    cv2.setTrackbarPos("Low L", "Color Picker", low_L)
                    # Update the 'High L' trackbar's visual position.
                    cv2.setTrackbarPos("High L", "Color Picker", high_L)
                    # Update the 'Low A' trackbar's visual position.
                    cv2.setTrackbarPos("Low A", "Color Picker", low_A)
                    # Update the 'High A' trackbar's visual position.
                    cv2.setTrackbarPos("High A", "Color Picker", high_A)
                    # Update the 'Low B' trackbar's visual position.
                    cv2.setTrackbarPos("Low B", "Color Picker", low_B)
                    # Update the 'High B' trackbar's visual position.
                    cv2.setTrackbarPos("High B", "Color Picker", high_B)
                    # Print confirmation.
                    print("Trackbars reset")
                # --- Clicked on the Save & Quit Button ---
                # If the button text is 'Save & Quit':
                elif text == "Save & Quit":
                    # Call the function to write the values to 'masks.py'.
                    save_masks()
                    # Release the camera resource.
                    cap.release()
                    # Close all OpenCV windows.
                    cv2.destroyAllWindows()
                    # Exit the script.
                    sys.exit(0)

# Assign the mouse callback function to the 'Buttons' window.
cv2.setMouseCallback("Buttons", mouse_callback)

# --- Main Loop ---
# Start the main infinite loop.
while True:
    # Read a frame from the camera.
    ret, frame = cap.read()
    # If reading the frame failed:
    if not ret:
        # Print an error message.
        print("Failed to read frame")
        # Break out of the loop.
        break

    # --- Color Filtering ---
    # Convert the BGR frame to the LAB color space.
    lab_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
    # Create a binary mask using the current (global) trackbar values.
    mask = cv2.inRange(lab_frame, (low_L, low_A, low_B), (high_L, high_A, high_B))
    # Apply the mask to the original frame.
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # Display the masked result in the 'Color Picker' window.
    cv2.imshow("Color Picker", result)
    # Display the (static) button image in the 'Buttons' window.
    cv2.imshow("Buttons", buttons_img)

    # Wait for 1ms for a key press; check if the 'Esc' key (ASCII 27) was pressed.
    if cv2.waitKey(1) & 0xFF == 27:
        # If 'Esc' was pressed, break out of the loop.
        break

# Release the camera resource.
cap.release()
# Close all OpenCV windows.
cv2.destroyAllWindows()