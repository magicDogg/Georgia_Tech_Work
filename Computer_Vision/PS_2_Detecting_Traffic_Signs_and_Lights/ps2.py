"""
CS6476 Problem Set 2 imports. Only Numpy and cv2 are allowed.
"""
import cv2
import numpy as np


def traffic_light_detection(img_in, radii_range):
    """Finds the coordinates of a traffic light image given a radii
    range.

    Use the radii range to find the circles in the traffic light and
    identify which of them represents the yellow light.

    Analyze the states of all three lights and determine whether the
    traffic light is red, yellow, or green. This will be referred to
    as the 'state'.

    It is recommended you use Hough tools to find these circles in
    the image.

    The input image may be just the traffic light with a white
    background or a larger image of a scene containing a traffic
    light.

    Args:
        img_in (numpy.array): image containing a traffic light.
        radii_range (list): range of radii values to search for.

    Returns:
        tuple: 2-element tuple containing:
        coordinates (tuple): traffic light center using the (x, y)
                             convention.
        state (str): traffic light state. A value in {'red', 'yellow',
                     'green'}
    """
    img_temp = np.copy(img_in)
    image_cols, image_rows, _ = img_temp.shape
    img_canny = cv2.Canny(img_temp, 110, 60)
    circles = cv2.HoughCircles(img_canny, cv2.HOUGH_GRADIENT, 1, 20, param1=50, param2=30,
                               minRadius=radii_range[0]-5, maxRadius=radii_range[-1]+16)

    if circles is None:
        return (0, 0), 'null'
    circles = circles[0]

    # Instead, pick the 3 similar ones with x value
    for i in range(len(circles)):
        curr_x = circles[i][0]
        curr_r = circles[i][2]
        candidates = []
        for j in range(len(circles)):
            other_x = circles[j][0]
            other_r = circles[j][2]
            if np.linalg.norm(curr_r - other_r) < 10 and np.linalg.norm(curr_x - other_x) < 10:
                candidates.append(j)
        if len(candidates) == 3:
            break

    if len(candidates) != 3:
        return (0, 0), 'null'

    tl_circles = []
    for index in candidates:
        tl_circles.append(circles[index])

    color = 'null'
    x_candidates = []
    y_candidates = []

    for circle in tl_circles:
        center_x = int(circle[0])
        center_y = int(circle[1])
        x_candidates.append(center_x)
        y_candidates.append(center_y)

        if img_temp[center_y, center_x, :][2] > 200 and img_temp[center_y, center_x, :][1] > 200 and img_temp[center_y, center_x, :][0] < 25:
            color = 'yellow'
        elif img_temp[center_y, center_x, :][2] > 250 and img_temp[center_y, center_x, :][1] < 200:
            color = 'red'
        elif img_temp[center_y, center_x, :][1] > 250 and img_temp[center_y, center_x, :][2] < 10:
            color = 'green'

    y_candidates.sort()

    return ((x_candidates[0], y_candidates[1]), color)


def yield_sign_detection(img_in):
    """Finds the centroid coordinates of a yield sign in the provided
    image.

    Args:
        img_in (numpy.array): image containing a traffic light.

    Returns:
        (x,y) tuple of coordinates of the center of the yield sign.
    """
    img_temp = np.copy(img_in)
    img_red = img_temp[:, :, 2]
    img_gre = img_temp[:, :, 1]
    img_blu = img_temp[:, :, 0]

    img_bi = np.zeros_like(img_red)
    img_bi[(img_red >= 200) & (img_red <= 255) & (img_gre >= 200) & (img_gre <= 255) & (img_blu >= 200)] = 255
    img_canny = cv2.Canny(img_bi, 110, 60)
    lines = cv2.HoughLinesP(img_canny, rho=1, theta=np.pi / 180 * 30, threshold=50, minLineLength=50, maxLineGap=4)

    if lines is None:
        return (0, 0)

    xmid, ymid = [], []

    for line in lines:
        line = line.flatten()

        line_length = np.sqrt((line[2] - line[0]) ** 2 + (line[3] - line[1]) ** 2)
        if (line[2] - line[0]) == 0:
            line_angle = 90
        else:
            line_angle = np.arctan((line[3] - line[1]) / (line[2] - line[0])) / np.pi * 180
        line_mid = ((line[2] + line[0]) / 2, (line[3] + line[1]) / 2)

        if (line_angle > 40 and line_angle < 80) or (line_angle < -40 and line_angle > -80):
            x1 = line[0]
            x2 = line[2]
            y1 = line[1]
            y2 = line[3]
            xmid.append((x1 + x2) / 2)
            ymid.append((y1 + y2) / 2)

    if len(xmid) == 0:
        return (0, 0)
    else:
        center = (int(np.mean(xmid)), int(np.mean(ymid) - 12))

        return center


def stop_sign_detection(img_in):
    """Finds the centroid coordinates of a stop sign in the provided
    image.

    Args:
        img_in (numpy.array): image containing a traffic light.

    Returns:
        (x,y) tuple of the coordinates of the center of the stop sign.
    """
    try:
        # define range of colors in HSV
        ranges = {
            'black': (np.array([0, 0, 0]), np.array([179, 50, 100])),
            'red': (np.array([-20, 100, 100]), np.array([13, 255, 255])),
            'dark_red': (np.array([0, 45, 45]), np.array([10, 255, 255])),
            'yellow': (np.array([20, 50, 150]), np.array([40, 255, 255])),
            'green': (np.array([50, 50, 150]), np.array([70, 255, 255])),
            'orange': (np.array([10, 50, 50]), np.array([20, 255, 255]))
        }

        # Threshold the HSV image to get[13, 255, 255] only relevant colors
        img_temp = np.copy(img_in)
        hsv = cv2.cvtColor(img_temp, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, ranges['dark_red'][0], ranges['dark_red'][1])
        mask = cv2.bitwise_and(img_temp, img_temp, mask=mask)
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

        # distinguish the yield red from the stop sign red
        mask[np.where((img_temp[:, :, 2] > 240))] = 0

        # dilate to get rid of noise + Brighten the mask
        mask = cv2.dilate(mask, np.ones((5, 5)))
        mask[mask > 20] = 255

        y, x = tuple(int(np.mean(i)) for i in np.where(mask > 250))

        return x, y
    except:
        return 0, 0


def warning_sign_detection(img_in):
    """Finds the centroid coordinates of a warning sign in the
    provided image.

    Args:
        img_in (numpy.array): image containing a traffic light.

    Returns:
        (x,y) tuple of the coordinates of the center of the sign.
    """
    img_temp = np.copy(img_in)
    img_red = img_temp[:, :, 2]
    img_gre = img_temp[:, :, 1]
    img_blu = img_temp[:, :, 0]

    img_bi = np.zeros_like(img_red)
    img_bi[(img_red >= 200) & (img_gre >= 200) & (img_blu < 10)] = 255
    img_canny = cv2.Canny(img_bi, 20, 0)

    lines = cv2.HoughLinesP(img_canny, rho=1, theta=np.pi / 180, threshold=20, minLineLength=30, maxLineGap=1)

    if lines is None:
        return (0, 0)
    else:
        xmid, ymid = [], []

        for line_packed in lines:
            line = line_packed.flatten()

            line_x_middle = (line[2] + line[0]) / 2
            line_y_middle = (line[3] + line[1]) / 2

            xmid.append(line_x_middle)
            ymid.append(line_y_middle)

        center = (int(np.mean(xmid)), int(np.mean(ymid)))

        return center


def construction_sign_detection(img_in):
    """Finds the centroid coordinates of a construction sign in the
    provided image.

    Args:
        img_in (numpy.array): image containing a traffic light.

    Returns:
        (x,y) tuple of the coordinates of the center of the sign.
    """
    img_temp = np.copy(img_in)
    img_red = img_temp[:, :, 2]
    img_gre = img_temp[:, :, 1]
    img_blu = img_temp[:, :, 0]

    img_bi = np.zeros_like(img_red)
    img_bi[(img_red >= 200) & (img_gre >= 100) & (img_gre < 200) & (img_blu < 25)] = 255
    img_canny = cv2.Canny(img_bi, 10, 0)

    lines = cv2.HoughLinesP(img_canny, rho=1, theta=np.pi / 180 * 45, threshold=20, minLineLength=40, maxLineGap=3)

    if lines is None:
        return (0, 0)
    else:
        xmid, ymid = [], []

        for line_packed in lines:
            line = line_packed.flatten()

            line_x_middle = (line[2] + line[0]) / 2
            line_y_middle = (line[3] + line[1]) / 2

            xmid.append(line_x_middle)
            ymid.append(line_y_middle)

        center = (int(np.mean(xmid)), int(np.mean(ymid)))

        return center


def do_not_enter_sign_detection(img_in):
    """Find the centroid coordinates of a do not enter sign in the
    provided image.

    Args:
        img_in (numpy.array): image containing a traffic light.

    Returns:
        (x,y) typle of the coordinates of the center of the sign.
    """
    img_temp = np.copy(img_in)
    img_red = img_temp[:, :, 2]
    img_gre = img_temp[:, :, 1]
    img_blu = img_temp[:, :, 0]

    img_bi = np.zeros_like(img_red)
    img_bi[(img_red >= 200) & (img_gre <= 10) & (img_gre <= 10)] = 255
    img_canny = cv2.Canny(img_bi, 120, 60)

    circles = cv2.HoughCircles(img_canny, cv2.HOUGH_GRADIENT, 1, 20,
                               param1=50, param2=30, minRadius=0, maxRadius=0)

    if circles is None:
        return (0, 0)
    else:
        for circle in circles[0]:
            center_x, center_y = int(circle[0]), int(circle[1])

            if (img_temp[center_y, center_x, :] >= 200).all():
                center = (center_x, center_y)
                return center

        return (0, 0)


def traffic_sign_detection(img_in):
    """Finds all traffic signs in a synthetic image.

    The image may contain at least one of the following:
    - traffic_light
    - no_entry
    - stop
    - warning
    - yield
    - construction

    Use these names for your output.

    See the instructions document for a visual definition of each
    sign.

    Args:
        img_in (numpy.array): input image containing at least one
                              traffic sign.

    Returns:
        dict: dictionary containing only the signs present in the
              image along with their respective centroid coordinates
              as tuples.

              For example: {'stop': (1, 3), 'yield': (4, 11)}
              These are just example values and may not represent a
              valid scene.
    """
    dict = {}

    img_tl = np.copy(img_in)
    radii_range = range(10, 30, 1)
    tl, color = traffic_light_detection(img_tl, radii_range)

    img_ne = np.copy(img_in)
    ne = do_not_enter_sign_detection(img_ne)

    img_st = np.copy(img_in)
    st = stop_sign_detection(img_st)

    img_wn = np.copy(img_in)
    wn = warning_sign_detection(img_wn)

    img_yd = np.copy(img_in)
    yd = yield_sign_detection(img_yd)

    img_cs = np.copy(img_in)
    cs = construction_sign_detection(img_cs)

    if tl != (0, 0):
        dict['traffic_light'] = tl
    if ne != (0, 0):
        dict['no_entry'] = ne
    if st != (0, 0):
        dict['stop'] = st
    if wn != (0, 0):
        dict['warning'] = wn
    if yd != (0, 0):
        dict['yield'] = yd
    if cs != (0, 0):
        dict['construction'] = cs

    return dict


def traffic_sign_detection_noisy(img_in):
    """Finds all traffic signs in a synthetic noisy image.

    The image may contain at least one of the following:
    - traffic_light
    - no_entry
    - stop
    - warning
    - yield
    - construction

    Use these names for your output.

    See the instructions document for a visual definition of each
    sign.

    Args:
        img_in (numpy.array): input image containing at least one
                              traffic sign.

    Returns:
        dict: dictionary containing only the signs present in the
              image along with their respective centroid coordinates
              as tuples.

              For example: {'stop': (1, 3), 'yield': (4, 11)}
              These are just example values and may not represent a
              valid scene.
    """
    dict = {}

    img_temp = np.copy(img_in)
    img_pre = cv2.fastNlMeansDenoisingColored(img_temp, None, 10, 10, 7, 21)
    cv2.imwrite("test.png", img_pre)

    radii_range = range(10, 30, 1)
    tl, color = traffic_light_detection(img_pre, radii_range)

    img_ne = np.copy(img_pre)
    ne = do_not_enter_sign_detection(img_ne)

    img_st = np.copy(img_pre)
    st = stop_sign_detection(img_st)

    img_wn = np.copy(img_pre)
    wn = warning_sign_detection(img_wn)

    img_yd = np.copy(img_pre)
    yd = yield_sign_detection(img_yd)

    img_cs = np.copy(img_pre)
    cs = construction_sign_detection(img_cs)

    if tl != (0, 0):
        dict['traffic_light'] = tl
    if ne != (0, 0):
        dict['no_entry'] = ne
    if st != (0, 0):
        dict['stop'] = st
    if wn != (0, 0):
        dict['warning'] = wn
    if yd != (0, 0):
        dict['yield'] = yd
    if cs != (0, 0):
        dict['construction'] = cs

    return dict


def traffic_sign_detection_challenge(img_in):
    """Finds traffic signs in an real image

    See point 5 in the instructions for details.

    Args:
        img_in (numpy.array): input image containing at least one
                              traffic sign.

    Returns:
        dict: dictionary containing only the signs present in the
              image along with their respective centroid coordinates
              as tuples.

              For example: {'stop': (1, 3), 'yield': (4, 11)}
              These are just example values and may not represent a
              valid scene.
    """
    raise NotImplementedError
