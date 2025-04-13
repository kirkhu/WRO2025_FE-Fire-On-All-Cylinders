import cv2
import numpy as np
import serial as AC
import struct
import pickle

# Load HSV values from the saved file
with open('hsv_values.pkl', 'rb') as f:
    hsv_values = pickle.load(f)


color_ranges = {
    'Orange': (hsv_values['Orange'][0], hsv_values['Orange'][1], (0, 165, 255)),
    'Blue': (hsv_values['Blue'][0], hsv_values['Blue'][1], (255, 0, 0))
}
color_ranges_final = {
    'Orange': (hsv_values['Orange'][0], hsv_values['Orange'][1], (0, 165, 255)),
    'Blue': (hsv_values['Blue'][0], hsv_values['Blue'][1], (255, 0, 0)),
    'Red': (hsv_values['Red'][0], hsv_values['Red'][1], (0, 0, 255)),
    'Green': (hsv_values['Green'][0], hsv_values['Green'][1], (0, 255, 0)),
    'Pink': (hsv_values['Pink'][0], hsv_values['Pink'][1], (255, 192, 203))
}

current_last = 0
def process_roi(undistorted_frame, x1, y1, x2, y2, threshold_value=90):
    roi = undistorted_frame[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    # Find all contours.
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # If there are contours, find the one with the largest area.
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        black_pixels = int(cv2.contourArea(largest_contour))  # Convert black pixels to integers.
        # Draw the largest outline.
        cv2.drawContours(binary, [largest_contour], -1, (255, 255, 255), -1)
    else:
        black_pixels = 0

    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR), black_pixels

def detect_color(undistorted_frame):
    hsv_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2HSV)
    color_y_positions = []

    for color, (lower, upper, bgr) in color_ranges.items():
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        color_mask = cv2.inRange(hsv_frame, lower, upper)
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest_contour) > 500:  # Filter out small-area noise.
                x, y, w, h = cv2.boundingRect(largest_contour)
                center_y = y + h // 2
                cv2.rectangle(undistorted_frame, (x, y), (x + w, y + h), bgr, 2)
                cv2.circle(undistorted_frame, (x + w // 2, center_y), 5, bgr, -1)  # Mark the center point.
                color_y_positions.append(center_y)
            else:
                color_y_positions.append(0)  # If no valid contour is found, return 0.
        else:
            color_y_positions.append(0)  # If no contour is found, return 0.

    return color_y_positions

def pd_control(target, current, kp, kd):
    global current_last  # Use global variables.
    error = current - target
    derivative = current - current_last
    control_signal = -(kp * error + kd * derivative)
    current_last =  current  # Update current_last before the return.
    return control_signal
def draw_multiple_curves(undistorted_frame, start_points, end_points, slope_values, curvature_factors, colors, thickness=2):
    """
    Draw multiple curves on the image with different starting points, endpoints, slopes, and curvatures, and return a list of coordinates for the red curves.
    """
    red_curve_points = []  #Used to store the coordinates of points on the red curves.
    green_curve_points = []  # Used to store the coordinates of points on the green curves.


    for start_point, end_point, slope, curvature, color in zip(start_points, end_points, slope_values, curvature_factors, colors):
        x1, y1 = start_point
        x2, y2 = end_point

        # Calculate the position of the middle control point to control the curvature.
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        control_x = mid_x
        control_y = int(mid_y - curvature * slope * (x2 - x1))  # Use curvature and slope to adjust the middle control point.

        # Use Bézier curves for drawing.
        curve_points = []
        for t in np.linspace(0, 1, 100):
            xt = (1 - t)**2 * x1 + 2 * (1 - t) * t * control_x + t**2 * x2
            yt = (1 - t)**2 * y1 + 2 * (1 - t) * t * control_y + t**2 * y2
            curve_points.append((int(xt), int(yt)))

        # If it is a red curve, save the point coordinates.
        if color == (0, 0, 255):  # Red curve.
            red_curve_points = curve_points
        if color == (0, 255, 0):  # green curve.
            green_curve_points = curve_points

        # Draw the curve.
        for i in range(len(curve_points) - 1):
            cv2.line(undistorted_frame, curve_points[i], curve_points[i + 1], color, thickness)

    return red_curve_points,green_curve_points  # Return the point coordinates of the red curve.


def detect_color_final(undistorted_frame, last_red_x_diff, last_green_x_diff, last_pink_red_x_diff, last_pink_green_x_diff, start_points, end_points, slope_values, curvature_factors, colors):
    """Detect areas of a specific color and return the Y-coordinate of the color’s center point. Calculate the X-coordinate difference between the red curve point and the red center point, and for green, use the center point X minus the function X."""
    hsv_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2HSV)
    color_y_positions = []
    pink_positions = [0] * 4
    center_x = 0
    center_y = 0
    red_x_diff = 0 
    green_x_diff = 0  
    pink_red_x_diff = 0  
    pink_green_x_diff = 0  
    

    # Color detection.
    for color, (lower, upper, bgr) in color_ranges_final.items():
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        color_mask = cv2.inRange(hsv_frame, lower, upper)
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            if color == 'Pink':
                # For pink, find the two largest color blocks.
                sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
                top_two_contours = [cnt for cnt in sorted_contours[:2] if cv2.contourArea(cnt) > 500]

                if len(top_two_contours) > 0:
                    # Update the position of the first largest color block.
                    x1, y1, w1, h1 = cv2.boundingRect(top_two_contours[0])
                    center_x1 = x1 + w1 // 2
                    center_y1 = y1 + h1 // 2
                    pink_positions[0] = center_x1
                    pink_positions[1] = center_y1

                    # Draw a rectangular box around the largest color block and mark the center point corresponding to the color.
                    cv2.rectangle(undistorted_frame, (x1, y1), (x1 + w1, y1 + h1), bgr, 2)
                    cv2.circle(undistorted_frame, (center_x1, center_y1), 5, bgr, -1)

                    if len(top_two_contours) > 1:
                        # Update the position of the second largest color block.
                        x2, y2, w2, h2 = cv2.boundingRect(top_two_contours[1])
                        center_x2 = x2 + w2 // 2
                        center_y2 = y2 + h2 // 2
                        pink_positions[2] = center_x2
                        pink_positions[3] = center_y2

                        # Draw a rectangular box around the second largest color block and mark the center point corresponding to the color.
                        cv2.rectangle(undistorted_frame, (x2, y2), (x2 + w2, y2 + h2), bgr, 2)
                        cv2.circle(undistorted_frame, (center_x2, center_y2), 5, bgr, -1)
                else:
                    # If there is no valid color block, set the pink coordinates to 0.
                    pink_positions[:] = [0, 0, 0, 0]
            else:
                # For other colors, only find the largest contour.
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 600:  # Filter out small-area noise.
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    center_x = x + w // 2
                    center_y = y + h // 2
                    color_y_positions.append(center_y)

                    # Draw a rectangular box and the center point corresponding to the color.
                    cv2.rectangle(undistorted_frame, (x, y), (x + w, y + h), bgr, 2)
                    cv2.circle(undistorted_frame, (center_x, center_y), 5, bgr, -1)
                else:
                    color_y_positions.append(0)  # No contour found, return 0.

            # Use multiple different curves with dynamic starting and ending points.
            red_curve_points,green_curve_points = draw_multiple_curves(undistorted_frame, start_points, end_points, slope_values, curvature_factors, colors)


            # Check the intersection points between the red curve and the detection line, and calculate the X-coordinate difference between the red curve points and the center point.
            if color == 'Red':
                max_curve_y = max([pt[1] for pt in red_curve_points])  # Get the highest point of the red curve.
                if center_y < max_curve_y:
                    for curve_x, curve_y in red_curve_points:
                        if abs(curve_y - center_y) < 2:  # Find the intersection point between the red curve and the center point.
                            red_x_diff = curve_x - center_x  # Calculate the difference in the X-coordinates of the red points.
                            cv2.circle(undistorted_frame, (curve_x, curve_y), 6, (0, 0, 255), -1)  # 用红色标记交点
                            break
                    else:
                        red_x_diff = last_red_x_diff  # If there is no intersection point, use the value from the previous frame.
                else:
                    red_x_diff = 0  # If the center point is above the curve, set it to 0.

            # Check the intersection points between the green curve and the detection line, and calculate the difference between the green center point X and the curve point X.
            if color == 'Green':
                max_curve_y = max([pt[1] for pt in green_curve_points])  # 获取绿色曲线的最高点
                if center_y < max_curve_y:
                    for curve_x, curve_y in green_curve_points:
                        if abs(curve_y - center_y) < 2:  # 查找绿色曲线和中心点的交点
                            green_x_diff = center_x - curve_x  # Calculate the difference in the X-coordinates of the green points.
                            cv2.circle(undistorted_frame, (curve_x, curve_y), 6, (0, 255, 0), -1)  # 用绿色标记交点
                            break
                    else:
                        green_x_diff = last_green_x_diff  # If there is no intersection point, use the value from the previous frame.
                else:
                    green_x_diff = 0  # If the center point is above the curve, set it to 0.
            # Check the intersection points between the pink curve and the detection line, and calculate the X-coordinate difference between the pink curve points and the center point.
            if color == 'Pink':
                pink_red_max_curve_y = max([pt[1] for pt in red_curve_points])  # Get the highest point of the red curve.
                pink_green_max_curve_y = max([pt[1] for pt in green_curve_points])  # 获取綠色曲线的最高点
                if pink_positions[1] < pink_red_max_curve_y:
                    for curve_x, curve_y in red_curve_points:
                        if abs(curve_y - pink_positions[1]) < 2:  # 查找红色曲线和中心点的交点
                            pink_red_x_diff = curve_x - pink_positions[0]  # Calculate the difference in the X-coordinates of the pink points.
                            cv2.circle(undistorted_frame, (curve_x, curve_y), 6, (255, 192, 203), -1)  # 用粉色标记交点
                            break
                    else:
                        pink_red_x_diff = last_pink_red_x_diff  # If there is no intersection point, use the value from the previous frame.
                else:
                    pink_red_x_diff = 0  # If the center point is above the curve, set it to 0.
                if pink_positions[1] < pink_green_max_curve_y:
                    for curve_x, curve_y in green_curve_points:
                        if abs(curve_y - pink_positions[1]) < 2:  # 查找綠色曲线和中心点的交点
                            pink_green_x_diff = pink_positions[0] - curve_x  # 计算粉綠色 X 坐标的差值
                            cv2.circle(undistorted_frame, (curve_x, curve_y), 6, (255, 192, 203), -1)  # 用粉色标记交点
                            break
                    else:
                        pink_green_x_diff = last_pink_green_x_diff  # If there is no intersection point, use the value from the previous frame.
                else:
                    pink_green_x_diff = 0  # If the center point is above the curve, set it to 0.

        else:
            color_y_positions.append(0)  # No contour found, return 0.
            pink_positions[:] = [0, 0, 0, 0]

    return color_y_positions, pink_positions, red_x_diff, green_x_diff, pink_red_x_diff, pink_green_x_diff  # 返回颜色中心的 Y 坐标和红绿 X 差值

