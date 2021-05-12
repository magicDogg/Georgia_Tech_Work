import math
import numpy as np
import cv2
import sys

# # Implement the functions below.


def extract_red(image):
    """ Returns the red channel of the input image. It is highly recommended to make a copy of the
    input image in order to avoid modifying the original array. You can do this by calling:
    temp_image = np.copy(image)

    Args:
        image (numpy.array): Input RGB (BGR in OpenCV) image.

    Returns:
        numpy.array: Output 2D array containing the red channel.
    """
    np_image = np.copy(image)

    return np_image[:, :, 2]


def extract_green(image):
    """ Returns the green channel of the input image. It is highly recommended to make a copy of the
    input image in order to avoid modifying the original array. You can do this by calling:
    temp_image = np.copy(image)

    Args:
        image (numpy.array): Input RGB (BGR in OpenCV) image.

    Returns:
        numpy.array: Output 2D array containing the green channel.
    """
    np_image = np.copy(image)

    return np_image[:, :, 1]


def extract_blue(image):
    """ Returns the blue channel of the input image. It is highly recommended to make a copy of the
    input image in order to avoid modifying the original array. You can do this by calling:
    temp_image = np.copy(image)

    Args:
        image (numpy.array): Input RGB (BGR in OpenCV) image.

    Returns:
        numpy.array: Output 2D array containing the blue channel.
    """
    np_image = np.copy(image)

    return np_image[:, :, 0]


def swap_green_blue(image):
    """ Returns an image with the green and blue channels of the input image swapped. It is highly
    recommended to make a copy of the input image in order to avoid modifying the original array.
    You can do this by calling:
    temp_image = np.copy(image)

    Args:
        image (numpy.array): Input RGB (BGR in OpenCV) image.

    Returns:
        numpy.array: Output 3D array with the green and blue channels swapped.
    """
    rgb_image = np.copy(image)
    blue_image = extract_blue(image)
    green_image = extract_green(image)
    rgb_image[:, :, 0] = green_image
    rgb_image[:, :, 1] = blue_image

    return rgb_image


def copy_paste_middle(src, dst, shape):
    """ Copies the middle region of size shape from src to the middle of dst. It is
    highly recommended to make a copy of the input image in order to avoid modifying the
    original array. You can do this by calling:
    temp_image = np.copy(image)

        Note: Assumes that src and dst are monochrome images, i.e. 2d arrays.

        Note: Where 'middle' is ambiguous because of any difference in the oddness
        or evenness of the size of the copied region and the image size, the function
        rounds downwards.  E.g. in copying a shape = (1,1) from a src image of size (2,2)
        into an dst image of size (3,3), the function copies the range [0:1,0:1] of
        the src into the range [1:2,1:2] of the dst.

    Args:
        src (numpy.array): 2D array where the rectangular shape will be copied from.
        dst (numpy.array): 2D array where the rectangular shape will be copied to.
        shape (tuple): Tuple containing the height (int) and width (int) of the section to be
                       copied.

    Returns:
        numpy.array: Output monochrome image (2D array)
    """
    src_image = np.copy(src)
    dst_image = np.copy(dst)

    target_half_height = int(shape[0]/2)
    target_half_width = int(shape[1]/2)

    src_height_center, src_width_center = np.floor(src_image.shape[0]/2), np.floor(src_image.shape[1]/2)
    dst_height_center, dst_width_center = np.floor(dst_image.shape[0]/2), np.floor(dst_image.shape[1]/2)

    src_center = src_image[src_height_center.astype(int)-target_half_height:src_height_center.astype(int)+target_half_height,
                           src_width_center.astype(int)-target_half_width:src_width_center.astype(int)+target_half_width]
    dst_image[dst_height_center.astype(int)-target_half_height:dst_height_center.astype(int)+target_half_height,
              dst_width_center.astype(int)-target_half_width:dst_width_center.astype(int)+target_half_width] = src_center

    return dst_image


def image_stats(image):
    """ Returns the tuple (min,max,mean,stddev) of statistics for the input monochrome image.
    In order to become more familiar with Numpy, you should look for pre-defined functions
    that do these operations i.e. numpy.min.

    It is highly recommended to make a copy of the input image in order to avoid modifying
    the original array. You can do this by calling:
    temp_image = np.copy(image)

    Args:
        image (numpy.array): Input 2D image.

    Returns:
        tuple: Four-element tuple containing:
               min (float): Input array minimum value.
               max (float): Input array maximum value.
               mean (float): Input array mean / average value.
               stddev (float): Input array standard deviation.
    """
    np_image = np.copy(image)
    f_min = np_image.min().astype(float)
    f_max = np_image.max().astype(float)
    f_mean = np_image.mean().astype(float)
    f_stddev = np.std(np_image).astype(float)

    return f_min, f_max, f_mean, f_stddev


def center_and_normalize(image, scale):
    """ Returns an image with the same mean as the original but with values scaled about the
    mean so as to have a standard deviation of "scale".

    Note: This function makes no defense against the creation
    of out-of-range pixel values.  Consider converting the input image to
    a float64 type before passing in an image.

    It is highly recommended to make a copy of the input image in order to avoid modifying
    the original array. You can do this by calling:
    temp_image = np.copy(image)

    Args:
        image (numpy.array): Input 2D image.
        scale (int or float): scale factor.

    Returns:
        numpy.array: Output 2D image.
    """
    np_image = np.copy(image).astype(float)
    np_image_mean = np_image.mean()
    np_image_stddev = np.std(np_image)
    np_image -= np_image_mean
    np_image /= np_image_stddev
    np_image *= scale
    np_image += np_image_mean

    return np_image


def shift_image_left(image, shift):
    """ Outputs the input monochrome image shifted shift pixels to the left.

    The returned image has the same shape as the original with
    the BORDER_REPLICATE rule to fill-in missing values.  See

    http://docs.opencv.org/2.4/doc/tutorials/imgproc/imgtrans/copyMakeBorder/copyMakeBorder.html?highlight=copy

    for further explanation.

    It is highly recommended to make a copy of the input image in order to avoid modifying
    the original array. You can do this by calling:
    temp_image = np.copy(image)

    Args:
        image (numpy.array): Input 2D image.
        shift (int): Displacement value representing the number of pixels to shift the input image.
            This parameter may be 0 representing zero displacement.

    Returns:
        numpy.array: Output shifted 2D image.
    """
    original_image = np.copy(image)
    shifted_image = np.zeros(original_image.shape)
    border = original_image[:, original_image.shape[1]-1]
    shifted_image[:, 0:original_image.shape[1]-shift-1] = original_image[:, shift:original_image.shape[1]-1]
    for i in range(original_image.shape[1]-shift-1, original_image.shape[1]):
        shifted_image[:, i] = border

    return shifted_image


def difference_image(img1, img2):
    """ Returns the difference between the two input images (img1 - img2). The resulting array must be normalized
    and scaled to fit [0, 255].

    It is highly recommended to make a copy of the input image in order to avoid modifying
    the original array. You can do this by calling:
    temp_image = np.copy(image)

    Args:
        img1 (numpy.array): Input 2D image.
        img2 (numpy.array): Input 2D image.

    Returns:
        numpy.array: Output 2D image containing the result of subtracting img2 from img1.
    """
    np_img1 = np.copy(img1)
    np_img2 = np.copy(img2)

    img_difference = np_img1 - np_img2
    img_normalized_diff = cv2.normalize(img_difference, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_64F)

    return img_normalized_diff


def add_noise(image, channel, sigma):
    """ Returns a copy of the input color image with Gaussian noise added to
    channel (0-2). The Gaussian noise mean must be zero. The parameter sigma
    controls the standard deviation of the noise.

    The returned array values must not be clipped or normalized and scaled. This means that
    there could be values that are not in [0, 255].

    Note: This function makes no defense against the creation
    of out-of-range pixel values.  Consider converting the input image to
    a float64 type before passing in an image.

    It is highly recommended to make a copy of the input image in order to avoid modifying
    the original array. You can do this by calling:
    temp_image = np.copy(image)

    Args:
        image (numpy.array): input RGB (BGR in OpenCV) image.
        channel (int): Channel index value.
        sigma (float): Gaussian noise standard deviation.

    Returns:
        numpy.array: Output 3D array containing the result of adding Gaussian noise to the
            specified channel.
    """
    np_image = np.copy(image).astype(float)
    np_image_channel = np_image[:, :, channel]
    gauss_noise = np.random.normal(0, sigma, np_image_channel.shape)
    gauss_noise = gauss_noise.reshape(np_image_channel.shape)
    np_image[:, :, channel] += gauss_noise

    return np_image
