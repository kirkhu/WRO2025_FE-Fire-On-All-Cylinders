import cv2
import numpy as np
import serial as AC
import struct


color_ranges = {
    'Orange': ([10, 210, 140], [15, 245, 220], (0, 165, 255)),
    'Blue': ([100, 113, 90], [113, 255, 202], (255, 0, 0))
}
color_ranges_final = {
    'Orange': ([10, 185, 115], [25, 255, 170], (0, 165, 255)),
    'Blue': ([105, 175, 80], [115, 240, 140], (255, 0, 0)),
    'Red': ([0, 110, 85], [5, 255, 165], (0, 0, 255)),
    'Green': ([45, 95, 90], [65, 180, 165], (0, 255, 0)),
    'Pink': ([160, 80, 64], [175, 175, 190], (255, 192, 203))
}

current_last = 0
def process_roi(undistorted_frame, x1, y1, x2, y2, threshold_value=90):
    roi = undistorted_frame[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    # Find all contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # If there are contours, find the largest contour
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        black_pixels = int(cv2.contourArea(largest_contour))  # Convert black pixels to integer
        # Draw the largest contour
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
            if cv2.contourArea(largest_contour) > 500:  # Filter out small noise areas
                x, y, w, h = cv2.boundingRect(largest_contour)
                center_y = y + h // 2
                cv2.rectangle(undistorted_frame, (x, y), (x + w, y + h), bgr, 2)
                cv2.circle(undistorted_frame, (x + w // 2, center_y), 5, bgr, -1)  # Mark the center point
                color_y_positions.append(center_y)
            else:
                color_y_positions.append(0)  # If no valid contours, return 0
        else:
            color_y_positions.append(0)  # If no contours found, return 0

    return color_y_positions

def pd_control(target, current, kp, kd):
    global current_last  # Use global variable
    error = current - target
    derivative = current - current_last
    control_signal = -(kp * error + kd * derivative)
    current_last =  current  # Update current_last before returning
    return control_signal
def draw_multiple_curves(undistorted_frame, start_points, end_points, slope_values, curvature_factors, colors, thickness=2):
    """
    Draw multiple curves with different start points, end points, slopes, and curvatures on the image, and return the coordinates of the red curve.
    """
    red_curve_points = []  # Used to save the coordinates of the red curve
    green_curve_points = []  # Used to save the coordinates of the green curve


    for start_point, end_point, slope, curvature, color in zip(start_points, end_points, slope_values, curvature_factors, colors):
        x1, y1 = start_point
        x2, y2 = end_point

        # Calculate the position of the control point in the middle to control the curvature
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        control_x = mid_x
        control_y = int(mid_y - curvature * slope * (x2 - x1))  # Adjust the middle control point using curvature and slope

        # Use Bezier curve to draw
        curve_points = []
        for t in np.linspace(0, 1, 100):
            xt = (1 - t)**2 * x1 + 2 * (1 - t) * t * control_x + t**2 * x2
            yt = (1 - t)**2 * y1 + 2 * (1 - t) * t * control_y + t**2 * y2
            curve_points.append((int(xt), int(yt)))

        # If it is a red curve, save the coordinates
        if color == (0, 0, 255):  # Red curve
            red_curve_points = curve_points
        if color == (0, 255, 0):  # Green curve
            green_curve_points = curve_points

        # Draw the curve
        for i in range(len(curve_points) - 1):
            cv2.line(undistorted_frame, curve_points[i], curve_points[i + 1], color, thickness)

    return red_curve_points, green_curve_points  # Return the coordinates of the red curve


def detect_color_final(undistorted_frame, last_red_x_diff, last_green_x_diff, last_pink_red_x_diff, last_pink_green_x_diff, start_points, end_points, slope_values, curvature_factors, colors):
    """Detect specific color regions and return the Y coordinates of the color center points, and calculate the X coordinate difference between the red curve point and the red center point, and the green as the center point X minus the function X"""
    hsv_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2HSV)
    color_y_positions = []
    pink_positions = [0] * 4
    center_x = 0
    center_y = 0
    red_x_diff = 0  # Default set to 0
    green_x_diff = 0  # Default set to 0
    pink_red_x_diff = 0  # Default set to 0
    pink_green_x_diff = 0  # Default set to 0
    

    # Color detection
    for color, (lower, upper, bgr) in color_ranges_final.items():
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        color_mask = cv2.inRange(hsv_frame, lower, upper)
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            if color == 'Pink':
                # For Pink, find the two largest color blocks
                sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
                top_two_contours = [cnt for cnt in sorted_contours[:2] if cv2.contourArea(cnt) > 500]

                if len(top_two_contours) > 0:
                    # Update the position of the first largest color block
                    x1, y1, w1, h1 = cv2.boundingRect(top_two_contours[0])
                    center_x1 = x1 + w1 // 2
                    center_y1 = y1 + h1 // 2
                    pink_positions[0] = center_x1
                    pink_positions[1] = center_y1

                    # Draw the rectangle of the largest color block and its center point
                    cv2.rectangle(undistorted_frame, (x1, y1), (x1 + w1, y1 + h1), bgr, 2)
                    cv2.circle(undistorted_frame, (center_x1, center_y1), 5, bgr, -1)

                    if len(top_two_contours) > 1:
                        # Update the position of the second largest color block
                        x2, y2, w2, h2 = cv2.boundingRect(top_two_contours[1])
                        center_x2 = x2 + w2 // 2
                        center_y2 = y2 + h2 // 2
                        pink_positions[2] = center_x2
                        pink_positions[3] = center_y2

                        # Draw the rectangle of the second largest color block and its center point
                        cv2.rectangle(undistorted_frame, (x2, y2), (x2 + w2, y2 + h2), bgr, 2)
                        cv2.circle(undistorted_frame, (center_x2, center_y2), 5, bgr, -1)
                else:
                    # If no valid color block, set pink coordinates to 0
                    pink_positions[:] = [0, 0, 0, 0]
            else:
                # For other colors, just find the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 600:  # Filter small noise areas
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    center_x = x + w // 2
                    center_y = y + h // 2
                    color_y_positions.append(center_y)

                    # Draw the rectangle and the color's center point
                    cv2.rectangle(undistorted_frame, (x, y), (x + w, y + h), bgr, 2)
                    cv2.circle(undistorted_frame, (center_x, center_y), 5, bgr, -1)
                else:
                    color_y_positions.append(0)  # No contour found, return 0

            # Use multiple different curves with dynamic start and end points
            red_curve_points, green_curve_points = draw_multiple_curves(undistorted_frame, start_points, end_points, slope_values, curvature_factors, colors)


            # Check for intersection points between the red curve and the detected horizontal line and calculate the X coordinate difference
            if color == 'Red':
                max_curve_y = max([pt[1] for pt in red_curve_points])  # Get the highest point of the red curve
                if center_y < max_curve_y:
                    for curve_x, curve_y in red_curve_points:
                        if abs(curve_y - center_y) < 2:  # Find the intersection point between the red curve and center point
                            red_x_diff = curve_x - center_x  # Calculate the difference in X coordinates
                            cv2.circle(undistorted_frame, (curve_x, curve_y), 6, (0, 0, 255), -1)  # Mark the intersection with red
                            break
                    else:
                        red_x_diff = last_red_x_diff  # If no intersection, use the previous value
                else:
                    red_x_diff = 0  # If the center point is higher than the curve, set to 0

            # Check for intersection points between the green curve and the detected horizontal line and calculate the center X coordinate minus curve X
            if color == 'Green':
                max_curve_y = max([pt[1] for pt in green_curve_points])  # Get the highest point of the green curve
                if center_y < max_curve_y:
                    for curve_x, curve_y in green_curve_points:
                        if abs(curve_y - center_y) < 2:  # Find the intersection point between the green curve and center point
                            green_x_diff = center_x - curve_x  # Calculate the difference in X coordinates
                            cv2.circle(undistorted_frame, (curve_x, curve_y), 6, (0, 255, 0), -1)  # Mark the intersection with green
                            break
                    else:
                        green_x_diff = last_green_x_diff  # If no intersection, use the previous value
                else:
                    green_x_diff = 0  # If the center point is higher than the curve, set to 0
            # Check for intersection points between the pink curve and the detected horizontal line and calculate the pink curve point and center X difference
            if color == 'Pink':
                pink_red_max_curve_y = max([pt[1] for pt in red_curve_points])  # Get the highest point of the red curve
                pink_green_max_curve_y = max([pt[1] for pt in green_curve_points])  # Get the highest point of the green curve
                if pink_positions[1] < pink_red_max_curve_y:
                    for curve_x, curve_y in red_curve_points:
                        if abs(curve_y - pink_positions[1]) < 2:  # Find the intersection point between the red curve and the center point
                            pink_red_x_diff = curve_x - pink_positions[0]  # Calculate the difference in X coordinates
                            cv2.circle(undistorted_frame, (curve_x, curve_y), 6, (255, 192, 203), -1)  # Mark the intersection with pink
                            break
                    else:
                        pink_red_x_diff = last_pink_red_x_diff  # If no intersection, use the previous value
                else:
                    pink_red_x_diff = 0  # If the center point is higher than the curve, set to 0
                if pink_positions[1] < pink_green_max_curve_y:
                    for curve_x, curve_y in green_curve_points:
                        if abs(curve_y - pink_positions[1]) < 2:  # Find the intersection point between the green curve and the center point
                            pink_green_x_diff = pink_positions[0] - curve_x  # Calculate the difference in X coordinates
                            cv2.circle(undistorted_frame, (curve_x, curve_y), 6, (255, 192, 203), -1)  # Mark the intersection with pink
                            break
                    else:
                        pink_green_x_diff = last_pink_green_x_diff  # If no intersection, use the previous value
                else:
                    pink_green_x_diff = 0  # If the center point is higher than the curve, set to 0

        else:
            color_y_positions.append(0)  # No contour found, return 0
            pink_positions[:] = [0, 0, 0, 0]

    return color_y_positions, pink_positions, red_x_diff, green_x_diff, pink_red_x_diff, pink_green_x_diff  # Return the Y coordinates of the color center and the X differences for red and green
