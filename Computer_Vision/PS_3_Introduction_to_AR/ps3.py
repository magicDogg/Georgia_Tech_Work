"""
CS6476 Problem Set 3 imports. Only Numpy and cv2 are allowed.
"""
import cv2
import numpy as np
from scipy.ndimage import rotate


def euclidean_distance(p0, p1):
    """Gets the distance between two (x,y) points

    Args:
        p0 (tuple): Point 1.
        p1 (tuple): Point 2.

    Return:
        float: The distance between points
    """
    (x0, y0) = p0
    (x1, y1) = p1

    distance = np.sqrt((x0 - x1)**2 + (y0 - y1)**2)

    return distance


def get_corners_list(image):
    """Returns a ist of image corner coordinates used in warping.

    These coordinates represent four corner points that will be projected to
    a target image.

    Args:
        image (numpy.array): image array of float64.

    Returns:
        list: List of four (x, y) tuples
            in the order [top-left, bottom-left, top-right, bottom-right].
    """
    corners = []
    img_temp = np.copy(image)
    height, width = img_temp.shape[0], img_temp.shape[1]

    top_left = (0, 0)
    top_right = (width - 1, 0)
    bottom_left = (0, height - 1)
    bottom_right = (width - 1, height - 1)

    corners.append(top_left)
    corners.append(bottom_left)
    corners.append(top_right)
    corners.append(bottom_right)

    return corners


def find_markers(image, template=None):
    """Finds four corner markers.

    Use a combination of circle finding, corner detection and convolution to
    find the four markers in the image.

    Args:
        image (numpy.array): image array of uint8 values.
        template (numpy.array): template image of the markers.

    Returns:
        list: List of four (x, y) tuples
            in the order [top-left, bottom-left, top-right, bottom-right].
    """
    img_temp = np.copy(image)
    blue_mark = np.copy(image)

    gray = cv2.cvtColor(blue_mark, cv2.COLOR_BGR2GRAY)
    corner = cv2.cornerHarris(gray, 5, 5, 0.01)
    corner_dilated = cv2.dilate(corner, None)
    blue_mark[corner_dilated > 0.02 * corner_dilated.max()] = [255, 0, 0]

    max_value = 0
    coeff_computation = cv2.TM_CCOEFF_NORMED

    for degree in range(60):
        rotated_template = rotate(template, 3*degree, mode='constant', reshape=False)
        rotated_temp_matched = cv2.matchTemplate(img_temp, rotated_template, coeff_computation)

        if rotated_temp_matched.max() > max_value:
            max_value = rotated_temp_matched.max()
            result = rotated_temp_matched

    threshold = 25
    temp_h, temp_w, _ = template.shape
    corners_sorted, corners = [], []

    while len(corners) != 4:
        _, max_value, _, max_pt = cv2.minMaxLoc(result)
        result[max_pt[1], max_pt[0]] = 0
        curr_max = max_pt[0] + int(temp_w/2), max_pt[1] + int(temp_h/2)

        curr_max_validate = True
        for i in range(len(corners)):
            if euclidean_distance(curr_max, corners[i]) < threshold:
                curr_max_validate = False

        if curr_max_validate and blue_mark[curr_max[1], curr_max[0], 0] > 250:
            corners.append(curr_max)

    corners = sorted(corners)

    if corners[0][1] < corners[1][1]:
        top_left = corners[0]
        bottom_left = corners[1]
    else:
        top_left = corners[1]
        bottom_left = corners[0]

    if corners[2][1] < corners[3][1]:
        top_right = corners[2]
        bottom_right = corners[3]
    else:
        top_right = corners[3]
        bottom_right = corners[2]

    corners_sorted.append(top_left)
    corners_sorted.append(bottom_left)
    corners_sorted.append(top_right)
    corners_sorted.append(bottom_right)

    return corners_sorted


def draw_box(image, markers, thickness=1):
    """Draws lines connecting box markers.

    Use your find_markers method to find the corners.
    Use cv2.line, leave the default "lineType" and Pass the thickness
    parameter from this function.

    Args:
        image (numpy.array): image array of uint8 values.
        markers(list): the points where the markers were located.
        thickness(int): thickness of line used to draw the boxes edges.

    Returns:
        numpy.array: image with lines drawn.
    """
    img_temp = np.copy(image)
    green_marker = (0, 255, 0)

    cv2.line(img_temp, markers[0], markers[1], color=green_marker, thickness=thickness)
    cv2.line(img_temp, markers[0], markers[2], color=green_marker, thickness=thickness)
    cv2.line(img_temp, markers[3], markers[1], color=green_marker, thickness=thickness)
    cv2.line(img_temp, markers[3], markers[2], color=green_marker, thickness=thickness)

    return img_temp


def project_imageA_onto_imageB(imageA, imageB, homography):
    """Projects image A into the marked area in imageB.

    Using the four markers in imageB, project imageA into the marked area.

    Use your find_markers method to find the corners.

    Args:
        imageA (numpy.array): image array of uint8 values.
        imageB (numpy.array): image array of uint8 values.
        homography (numpy.array): Transformation matrix, 3 x 3.

    Returns:
        numpy.array: combined image
    """
    tempA, tempB = np.copy(imageA), np.copy(imageB)
    height_A, width_A, _ = tempA.shape
    height_B, width_B, _ = tempB.shape

    vector_in = np.zeros((3, height_A * width_A), np.int32)
    vector_in[2, :] = 1

    for x in range(width_A):
        vector_in[0, x * height_A: (x + 1) * height_A] = x
        vector_in[1, x * height_A: (x + 1) * height_A] = np.arange(height_A)

    vector_out = np.dot(homography, vector_in)
    vector_out[:, :] = vector_out[:, :] / vector_out[2, :]

    x_in = np.array(vector_in[0, :])
    y_in = np.array(vector_in[1, :])

    x_out = np.clip(np.array(vector_out[0, :]), 0, width_B-1).astype(int)
    y_out = np.clip(np.array(vector_out[1, :]), 0, height_B-1).astype(int)

    tempB[y_out, x_out, :] = tempA[y_in, x_in, :]

    return tempB


def find_four_point_transform(src_points, dst_points):
    """Solves for and returns a perspective transform.

    Each source and corresponding destination point must be at the
    same index in the lists.

    Do not use the following functions (you will implement this yourself):
        cv2.findHomography
        cv2.getPerspectiveTransform

    Hint: You will probably need to use least squares to solve this.

    Args:
        src_points (list): List of four (x,y) source points.
        dst_points (list): List of four (x,y) destination points.

    Returns:
        numpy.array: 3 by 3 homography matrix of floating point values.
    """
    PH = []
    for i in range(len(src_points)):
        x_s, y_s = src_points[i]
        x_d, y_d = dst_points[i]
        PH.append([x_s, y_s, 1, 0, 0, 0, -x_s * x_d, -y_s * x_d, -x_d])
        PH.append([0, 0, 0, x_s, y_s, 1, -x_s * y_d, -y_s * y_d, -y_d])

    U, Sigma, V = np.linalg.svd(np.asarray(PH))
    N = V[-1, :] / V[-1, -1]
    H = N.reshape(3, 3)

    return H


def video_frame_generator(filename):
    """A generator function that returns a frame on each 'next()' call.

    Will return 'None' when there are no frames left.

    Args:
        filename (string): Filename.

    Returns:
        None.
    """
    # Todo: Open file with VideoCapture and set result to 'video'. Replace None
    video = cv2.VideoCapture(filename)

    # Do not edit this while loop
    while video.isOpened():
        ret, frame = video.read()

        if ret:
            yield frame
        else:
            break

    # Todo: Close video (release) and yield a 'None' value. (add 2 lines)
    video.release()
    yield None
