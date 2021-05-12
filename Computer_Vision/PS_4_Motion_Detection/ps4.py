"""Problem Set 4: Motion Detection"""

import numpy as np
import cv2

# Utility function
def normalize_and_scale(image_in, scale_range=(0, 255)):
    """Normalizes and scales an image to a given range [0, 255].

    Utility function. There is no need to modify it.

    Args:
        image_in (numpy.array): input image.
        scale_range (tuple): range values (min, max). Default set to [0, 255].

    Returns:
        numpy.array: output image.
    """
    image_out = np.zeros(image_in.shape)
    cv2.normalize(image_in, image_out, alpha=scale_range[0],
                  beta=scale_range[1], norm_type=cv2.NORM_MINMAX)

    return image_out


def gradient_x(image):
    """Computes image gradient in X direction.

    Use cv2.Sobel to help you with this function. Additionally you
    should set cv2.Sobel's 'scale' parameter to one eighth and ksize
    to 3.

    Args:
        image (numpy.array): grayscale floating-point image with values in [0.0, 1.0].

    Returns:
        numpy.array: image gradient in the X direction. Output
                     from cv2.Sobel.
    """

    return cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3, scale=0.125)


def gradient_y(image):
    """Computes image gradient in Y direction.

    Use cv2.Sobel to help you with this function. Additionally you
    should set cv2.Sobel's 'scale' parameter to one eighth and ksize
    to 3.

    Args:
        image (numpy.array): grayscale floating-point image with values in [0.0, 1.0].

    Returns:
        numpy.array: image gradient in the Y direction.
                     Output from cv2.Sobel.
    """

    return cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3, scale=0.125)


def optic_flow_lk(img_a, img_b, k_size, k_type, sigma=1):
    """Computes optic flow using the Lucas-Kanade method.

    For efficiency, you should apply a convolution-based method.

    Note: Implement this method using the instructions in the lectures
    and the documentation.

    You are not allowed to use any OpenCV functions that are related
    to Optic Flow.

    Args:
        img_a (numpy.array): grayscale floating-point image with
                             values in [0.0, 1.0].
        img_b (numpy.array): grayscale floating-point image with
                             values in [0.0, 1.0].
        k_size (int): size of averaging kernel to use for weighted
                      averages. Here we assume the kernel window is a
                      square so you will use the same value for both
                      width and height.
        k_type (str): type of kernel to use for weighted averaging,
                      'uniform' or 'gaussian'. By uniform we mean a
                      kernel with the only ones divided by k_size**2.
                      To implement a Gaussian kernel use
                      cv2.getGaussianKernel. The autograder will use
                      'uniform'.
        sigma (float): sigma value if gaussian is chosen. Default
                       value set to 1 because the autograder does not
                       use this parameter.

    Returns:
        tuple: 2-element tuple containing:
            U (numpy.array): raw displacement (in pixels) along
                             X-axis, same size as the input images,
                             floating-point type.
            V (numpy.array): raw displacement (in pixels) along
                             Y-axis, same size and type as U.
    """
    filter_dim = (k_size, k_size)

    if k_type == 'gaussian':
        temp_a = cv2.GaussianBlur(img_a, ksize=filter_dim, sigmaX=sigma, sigmaY=sigma)
        temp_b = cv2.GaussianBlur(img_b, ksize=filter_dim, sigmaX=sigma, sigmaY=sigma)
    else:
        temp_a = np.copy(img_a)
        temp_b = np.copy(img_b)

    Ix, Iy = gradient_x(temp_a), gradient_y(temp_a)
    It = cv2.subtract(temp_a, temp_b).astype(np.float64)
    Ixx = cv2.boxFilter(Ix**2, -1, ksize=filter_dim, normalize=False)
    Iyy = cv2.boxFilter(Iy**2, -1, ksize=filter_dim, normalize=False)
    Ixy = cv2.boxFilter(Ix*Iy, -1, ksize=filter_dim, normalize=False)
    Ixt = cv2.boxFilter(Ix*It, -1, ksize=filter_dim, normalize=False)
    Iyt = cv2.boxFilter(Iy*It, -1, ksize=filter_dim, normalize=False)

    det = np.clip(Ixx * Iyy - Ixy ** 2, 0.000001, np.inf)
    temp_u, temp_v = (Iyy * (-Ixt) + (-Ixy) * (-Iyt)), ((-Ixy) * (-Ixt) + Ixx * (-Iyt))
    u, v = -np.where(det != 0, temp_u / det, 0), -np.where(det != 0, temp_v / det, 0)

    return u, v


def reduce_image(image):
    """Reduces an image to half its shape.

    The autograder will pass images with even width and height. It is
    up to you to determine values with odd dimensions. For example the
    output image can be the result of rounding up the division by 2:
    (13, 19) -> (7, 10)

    For simplicity and efficiency, implement a convolution-based
    method using the 5-tap separable filter.

    Follow the process shown in the lecture 6B-L3. Also refer to:
    -  Burt, P. J., and Adelson, E. H. (1983). The Laplacian Pyramid
       as a Compact Image Code
    You can find the link in the problem set instructions.

    Args:
        image (numpy.array): grayscale floating-point image, values in
                             [0.0, 1.0].

    Returns:
        numpy.array: output image with half the shape, same type as the
                     input image.
    """
    kernel = np.array([0.25 - 0.4 / 2.0, 0.25, 0.4, 0.25, 0.25 - 0.4 / 2.0])
    kernel_filter = np.outer(kernel, kernel)
    filtered_image = cv2.filter2D(image, -1, kernel_filter)
    reduced_filtered_image = filtered_image[::2, ::2]

    return reduced_filtered_image


def gaussian_pyramid(image, levels):
    """Creates a Gaussian pyramid of a given image.

    This method uses reduce_image() at each level. Each image is
    stored in a list of length equal the number of levels.

    The first element in the list ([0]) should contain the input
    image. All other levels contain a reduced version of the previous
    level.

    All images in the pyramid should floating-point with values in

    Args:
        image (numpy.array): grayscale floating-point image, values
                             in [0.0, 1.0].
        levels (int): number of levels in the resulting pyramid.

    Returns:
        list: Gaussian pyramid, list of numpy.arrays.
    """
    pyramid_list = [image]
    temp = np.copy(image)
    for i in range(1, levels):
        temp = reduce_image(temp)
        pyramid_list.append(temp)

    return pyramid_list


def create_combined_img(img_list):
    """Stacks images from the input pyramid list side-by-side.

    Ordering should be large to small from left to right.

    See the problem set instructions for a reference on how the output
    should look like.

    Make sure you call normalize_and_scale() for each image in the
    pyramid when populating img_out.

    Args:
        img_list (list): list with pyramid images.

    Returns:
        numpy.array: output image with the pyramid images stacked
                     from left to right.
    """
    reg_img = normalize_and_scale(img_list[0])
    out_img = np.zeros(shape=img_list[0].shape)

    for i in range(len(img_list)-1):
        height_1, width_1 = reg_img.shape
        height_2, width_2 = img_list[i+1].shape
        out_img = np.ones(shape=(np.max([height_1, height_2]), width_1 + width_2))
        out_img[:height_1, :width_1] = np.copy(reg_img)
        out_img[:height_2, width_1:(width_1 + width_2)] = normalize_and_scale(img_list[i+1])
        reg_img = np.copy(out_img)

    return out_img


def expand_image(image):
    """Expands an image doubling its width and height.

    For simplicity and efficiency, implement a convolution-based
    method using the 5-tap separable filter.

    Follow the process shown in the lecture 6B-L3. Also refer to:
    -  Burt, P. J., and Adelson, E. H. (1983). The Laplacian Pyramid
       as a Compact Image Code

    You can find the link in the problem set instructions.

    Args:
        image (numpy.array): grayscale floating-point image, values
                             in [0.0, 1.0].

    Returns:
        numpy.array: same type as 'image' with the doubled height and
                     width.
    """
    kernel = np.array([[0.125, 0.5, 0.75, 0.5, 0.125]], dtype=np.float64)
    kernel_filter = np.outer(kernel, kernel)
    expanded_image = np.zeros((len(image) * 2, len(image[0]) * 2), dtype=np.float64)
    expanded_image[::2, ::2] = image[:, :]
    expanded_filtered_image = cv2.filter2D(expanded_image, -1, kernel_filter, borderType=cv2.BORDER_REFLECT101)

    return expanded_filtered_image


def laplacian_pyramid(g_pyr):
    """Creates a Laplacian pyramid from a given Gaussian pyramid.

    This method uses expand_image() at each level.

    Args:
        g_pyr (list): Gaussian pyramid, returned by gaussian_pyramid().

    Returns:
        list: Laplacian pyramid, with l_pyr[-1] = g_pyr[-1].
    """
    pyramid_list = []

    for i in range(len(g_pyr)-1):
        gau_frame = g_pyr[i]
        lap_exp = expand_image(g_pyr[i + 1])

        if gau_frame.shape[0] < lap_exp.shape[0]:
            lap_exp = np.delete(lap_exp, (-1), axis=0)

        if gau_frame.shape[1] < lap_exp.shape[1]:
            lap_exp = np.delete(lap_exp, (-1), axis=1)

        pyramid_list.append(gau_frame - lap_exp)

    pyramid_list.append(g_pyr[-1])

    return pyramid_list


def warp(image, U, V, interpolation, border_mode):
    """Warps image using X and Y displacements (U and V).

    This function uses cv2.remap. The autograder will use cubic
    interpolation and the BORDER_REFLECT101 border mode. You may
    change this to work with the problem set images.

    See the cv2.remap documentation to read more about border and
    interpolation methods.

    Args:
        image (numpy.array): grayscale floating-point image, values
                             in [0.0, 1.0].
        U (numpy.array): displacement (in pixels) along X-axis.
        V (numpy.array): displacement (in pixels) along Y-axis.
        interpolation (Inter): interpolation method used in cv2.remap.
        border_mode (BorderType): pixel extrapolation method used in
                                  cv2.remap.

    Returns:
        numpy.array: warped image, such that
                     warped[y, x] = image[y + V[y, x], x + U[y, x]]
    """
    height, width = image.shape
    X, Y = np.meshgrid(range(width), range(height))
    X_mapping, Y_mapping = (X + U).astype(np.float32), (Y + V).astype(np.float32)
    warped = cv2.remap(image, X_mapping, Y_mapping, interpolation=interpolation, borderMode=border_mode)

    return warped


def hierarchical_lk(img_a, img_b, levels, k_size, k_type, sigma, interpolation,
                    border_mode):
    """Computes the optic flow using Hierarchical Lucas-Kanade.

    This method should use reduce_image(), expand_image(), warp(),
    and optic_flow_lk().

    Args:
        img_a (numpy.array): grayscale floating-point image, values in
                             [0.0, 1.0].
        img_b (numpy.array): grayscale floating-point image, values in
                             [0.0, 1.0].
        levels (int): Number of levels.
        k_size (int): parameter to be passed to optic_flow_lk.
        k_type (str): parameter to be passed to optic_flow_lk.
        sigma (float): parameter to be passed to optic_flow_lk.
        interpolation (Inter): parameter to be passed to warp.
        border_mode (BorderType): parameter to be passed to warp.

    Returns:
        tuple: 2-element tuple containing:
            U (numpy.array): raw displacement (in pixels) along X-axis,
                             same size as the input images,
                             floating-point type.
            V (numpy.array): raw displacement (in pixels) along Y-axis,
                             same size and type as U.
    """
    img_a_pyramid, img_b_pyramid = gaussian_pyramid(img_a, levels), gaussian_pyramid(img_b, levels)

    height, width = img_a.shape
    height, width = height // (2 ** (levels - 1)), width // (2 ** (levels - 1))

    U, V = np.zeros((height, width), dtype=np.float64), np.zeros((height, width), dtype=np.float64)

    for i in range(levels - 1, -1, -1):
        if i != levels - 1:
            U, V = 2*expand_image(U), 2*expand_image(V)

        img_A = img_a_pyramid[i]
        img_B = img_b_pyramid[i]
        img_B_wrap = img_B if (i == levels - 1) else warp(img_B, U, V, interpolation, border_mode)

        u, v = optic_flow_lk(img_A, img_B_wrap, k_size, k_type, sigma)
        U += u
        V += v

    return U, V
