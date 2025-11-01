<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Camera Selection</div>
  - In autonomous vehicle competitions, the selection of the camera module is crucial—indeed, it is the core element influencing the outcome of the race—to accurately capture and identify the various targets on the track, including the red/green posts, black boundary walls, magenta parking areas, as well as the blue and orange lines on the ground. We must select a camera module featuring high resolution, extremely low latency, and excellent high light sensitivity performance to ensure that image information is both real-time and clear, significantly enhancing the vehicle's recognition capability for surrounding obstacles. This directly optimizes subsequent avoidance and navigation decisions, establishing the vehicle's competitiveness on the track
  - Since we are using the NVIDIA Jetson Orin Nano as the main controller, we must choose a camera module that is compatible with the Jetson Nano to ensure normal functionality. The following is a comparison of camera modules commonly used in Taiwan.

- ### Comparison of Camera Modules
    <div align="center">
    <table>
    <tr align="center" >
    <th rowspan="2">Model</th> 
    <th >SONY IMX219</th>
    <th >SONY IMX477</th>
    </tr>
    <tr align="center">
    <td><img src="./img/SONY_IMX219.png" width="300" alt="SONY IMX219" /></td>
    <td><img src="./img/SONY_IMX477.png" width="300" alt="SONY IMX477" /></td>
    </tr>
    <tr align="center">
    <td>Sensor</td>
    <td>SONY IMX 219</td>
    <td>SONY IMX 477</td>
    </tr>
    <tr align="center">
    <td>FOV</td>
    <td>160 MAX</td>
    <td>160 MAX</td>
    </tr>
    <tr align="center">
    <td>Resolution</td>
    <td>3280 × 2464 pix</td>
    <td>4056 × 3040 pix</td>
    </tr>
    </tr>
    </table>
    </div>
  
    __Thus, in terms of resolution, the SONY IMX477 is our best choice for the competition environment.__

- ### Wide-angle lens distortion correction

  The purpose of wide-angle lens distortion correction is to reduce or eliminate the deformation effects produced when capturing images with a wide-angle lens. These deformations often include "barrel distortion" or "pincushion distortion," which cause straight objects in the image to appear curved or distorted. Through correction, images can be restored to proportions and shapes closer to reality, enhancing the accuracy and realism of the image. This is particularly suitable for applications requiring precise measurement or detailed capture, such as machine vision, architectural surveying, and autonomous driving technology.
  - ### Correction Methods
      When performing wide-angle lens distortion correction on the NVIDIA Jetson Orin Nano, the calibration functions in the OpenCV library are typically used. The basic steps are as follows:
    <ol>
    <div align="center">
    <li>
    
      __Capture Calibration Images:__ Place a checkerboard or dot array within the field of view of the wide-angle lens and capture multiple images from different angles. These images are used to calculate calibration parameters.</li>
    
    <table>
    <tr align="center" >
    <th >Checkerboard Image</th> 
    </tr>
    <tr align="center">
    <td><img src="./img/chessboard.png" width="300" alt="Chessboard" /></td>
    </tr>  
    </table>
    </div>
    <li>

    __Detect Checkerboard Corners:__ Use OpenCV's findChessboardCorners() function to automatically detect the corner positions of the checkerboard. For each calibration image, this step finds the corner coordinates needed for calculating the correction parameters.</li>
    
    <li>

    __Calculate Calibration Parameters:__ Use the calibrateCamera() function to calculate the camera's intrinsic parameters and distortion coefficients. These parameters include focal length, optical center, and radial and tangential distortion coefficients of the lens.</li>
   
    <li>

    __Apply Correction Parameters:__ In actual images, use the undistort() function to apply the correction parameters to each frame. This corrected image will reduce the distortion caused by the wide-angle lens, making the image closer to true proportions.</li>
    
    <li>

    __Real-Time Processing (If Needed):__ If real-time correction is required on the Jetson Nano, ensure efficiency in image processing. Given the limited performance of the NVIDIA Jetson Orin Nano, consider adjusting image resolution or optimizing processing steps to enhance correction speed.</li>

   __A simple code example is as follows:__
    - ### python Code-Python

          import cv2
          import numpy as np

          # Load calibration images

          images = ["image1.jpg", "image2.jpg", ...]  # Replace with your image paths
          chessboard_size = (9, 6)  # Chessboard dimensions
          obj_points = []  # Real world coordinates points
          img_points = []  # Image coordinates points

          # Define corner points for the chessboard

          objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
          objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)

          for image in images:
              img = cv2.imread(image)
              gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
              ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)
              
              if ret:
                  img_points.append(corners)
                  obj_points.append(objp)

          # Calibrate camera parameters

          ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, gray.shape[::-1], None, None)

          # Read the image to be undistorted


          img = cv2.imread('test_image.jpg')
          h, w = img.shape[:2]
          newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))

          # Apply distortion correction

          dst = cv2.undistort(img, mtx, dist, None, newcameramtx)

          # Crop the image

          x, y, w, h = roi
          dst = dst[y:y+h, x:x+w]

          cv2.imshow('Undistorted Image', dst)
          cv2.waitKey(0)
          cv2.destroyAllWindows()

      Experimental results indicate that setting the resolution to __640x480__ optimizes system performance. This configuration effectively reduces the computational load on the Jetson Nano while significantly enhancing the efficiency of image capture and recognition.  
     ### Comparison image of before and after correction
    
    <div align="center">
    <table>
    <tr align="center" >
    <th>Item</th>
    <th >Before</th>
    <th >After</th>
    </tr>
    <tr align="center">
    <th>Photo</th>
    <td><img src="./img/Camera_before.png" width="400" alt="Camera_Before" /></td>
    <td><img src="./img/Camera_after.png" width="400" alt="Camera_After" /></td>
    </tr>
    </table>
    </div>
# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  