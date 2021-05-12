"""Problem Set 6: PCA, Boosting, Haar Features, Viola-Jones."""
import numpy as np
import cv2
import os

from helper_classes import WeakClassifier, VJ_Classifier


# assignment code
def load_images(folder, size=(32, 32)):
    """Load images to workspace.

    Args:
        folder (String): path to folder with images.
        size   (tuple): new image sizes

    Returns:
        tuple: two-element tuple containing:
            X (numpy.array): data matrix of flatten images
                             (row:observations, col:features) (float).
            y (numpy.array): 1D array of labels (int).
    """
    images = [f for f in os.listdir(folder) if f.endswith(".png")]
    X, y = [], []

    for image in images:
        label_lab = image.split('.')[0][-2:]
        image_data = cv2.imread(os.path.join(folder, image))
        image_gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        image_reduced = cv2.resize(image_gray, tuple(size))
        image_flatten = image_reduced.flatten()

        X.append(image_flatten)
        y.append(int(label_lab))

    X, y = np.asarray(X), np.asarray(y)

    return X, y


def split_dataset(X, y, p):
    """Split dataset into training and test sets.

    Let M be the number of images in X, select N random images that will
    compose the training data (see np.random.permutation). The images that
    were not selected (M - N) will be part of the test data. Record the labels
    accordingly.

    Args:
        X (numpy.array): 2D dataset.
        y (numpy.array): 1D array of labels (int).
        p (float): Decimal value that determines the percentage of the data
                   that will be the training data.

    Returns:
        tuple: Four-element tuple containing:
            Xtrain (numpy.array): Training data 2D array.
            ytrain (numpy.array): Training data labels.
            Xtest (numpy.array): Test data test 2D array.
            ytest (numpy.array): Test data labels.
    """
    random_indices = np.random.permutation(len(X))
    N = int(len(X) * p)
    Xtrain, ytrain, Xtest, ytest = [], [], [], []

    for index in random_indices:
        if index < N:
            Xtrain.append(X[index])
            ytrain.append(y[index])
        else:
            Xtest.append(X[index])
            ytest.append(y[index])

    return np.asarray(Xtrain), np.asarray(ytrain), np.asarray(Xtest), np.asarray(ytest)


def get_mean_face(x):
    """Return the mean face.

    Calculate the mean for each column.

    Args:
        x (numpy.array): array of flattened images.

    Returns:
        numpy.array: Mean face.
    """

    return np.mean(x, axis=0)


def pca(X, k):
    """PCA Reduction method.

    Return the top k eigenvectors and eigenvalues using the covariance array
    obtained from X.


    Args:
        X (numpy.array): 2D data array of flatten images (row:observations,
                         col:features) (float).
        k (int): new dimension space

    Returns:
        tuple: two-element tuple containing
            eigenvectors (numpy.array): 2D array with the top k eigenvectors.
            eigenvalues (numpy.array): array with the top k eigenvalues.
    """
    M = get_mean_face(X)
    C = X - M
    V = np.cov(C.transpose(), bias=True)
    V = V * X.shape[0]
    e_values_full, e_vectors_full = np.linalg.eigh(V)

    idx = e_values_full.argsort()[::-1]
    e_values, e_vectors = e_values_full[idx], e_vectors_full[:, idx]

    return e_vectors[:, :k], e_values[:k]


class Boosting:
    """Boosting classifier.

    Args:
        X (numpy.array): Data array of flattened images
                         (row:observations, col:features) (float).
        y (numpy.array): Labels array of shape (observations, ).
        num_iterations (int): number of iterations
                              (ie number of weak classifiers).

    Attributes:
        Xtrain (numpy.array): Array of flattened images (float32).
        ytrain (numpy.array): Labels array (float32).
        num_iterations (int): Number of iterations for the boosting loop.
        weakClassifiers (list): List of weak classifiers appended in each
                               iteration.
        alphas (list): List of alpha values, one for each classifier.
        num_obs (int): Number of observations.
        weights (numpy.array): Array of normalized weights, one for each
                               observation.
        eps (float): Error threshold value to indicate whether to update
                     the current weights or stop training.
    """
    def __init__(self, X, y, num_iterations):
        self.Xtrain = np.float32(X)
        self.ytrain = np.float32(y)
        self.num_iterations = num_iterations
        self.weakClassifiers = []
        self.alphas = []
        self.num_obs = X.shape[0]
        self.weights = np.array([1.0 / self.num_obs] * self.num_obs)  # uniform weights
        self.eps = 0.0001

    def train(self):
        """Implement the for loop shown in the problem set instructions."""
        for j in range(self.num_iterations):
            # Step 1: Re-normalize the weights
            weights_total = np.sum(self.weights)
            self.weights = self.weights / weights_total

            # Step 2: Instantiate the weak classifier + Train it
            wkc = WeakClassifier(self.Xtrain, self.ytrain, self.weights, self.eps)
            wkc.train()

            # Step 3: Find error sum
            prediction, error_sum = [], 0
            for i in range(self.num_obs):
                prediction.append(wkc.predict(self.Xtrain[i]))
                index = self.ytrain[i] != prediction[i]
                error_sum += index * self.weights[i]
            self.weakClassifiers.append(wkc)

            # Step 4: Calculate the alpha
            self.alphas.append(0.5 * np.log((1. - error_sum) / error_sum))

            # Step 5: Update the weights until the error sum will get smaller than the eps
            if error_sum >= self.eps:
                for i in range(self.num_obs):
                    self.weights[i] = self.weights[i] * np.exp((-1) * self.ytrain[i] * self.alphas[j] * wkc.predict(self.Xtrain[i]))
            else:
                break

    def evaluate(self):
        """Return the number of correct and incorrect predictions.

        Use the training data (self.Xtrain) to obtain predictions. Compare
        them with the training labels (self.ytrain) and return how many
        where correct and incorrect.

        Returns:
            tuple: two-element tuple containing:
                correct (int): Number of correct predictions.
                incorrect (int): Number of incorrect predictions.
        """
        correct, incorrect = 0, 0
        y_train_predict = self.predict(self.Xtrain)
        for i in range(self.num_obs):
            if y_train_predict[i] == self.ytrain[i]:
                correct += 1
            else:
                incorrect += 1

        return correct, incorrect

    def predict(self, X):
        """Return predictions for a given array of observations.

        Use the alpha values stored in self.aphas and the weak classifiers
        stored in self.weakClassifiers.

        Args:
            X (numpy.array): Array of flattened images (observations).

        Returns:
            numpy.array: Predictions, one for each row in X.
        """
        weak_prediction_eval = []
        for j in range(len(self.alphas)):
            weak_prediction = []
            for i in range(X.shape[0]):
                weak_prediction.append(self.weakClassifiers[j].predict(X[i, :]))
            weak_prediction = np.asarray(weak_prediction)
            weak_prediction_eval.append(self.alphas[j] * weak_prediction)
        weak_prediction_eval_total = np.sign(np.sum(weak_prediction_eval, axis=0))

        return np.asarray(weak_prediction_eval_total)


class HaarFeature:
    """Haar-like features.

    Args:
        feat_type (tuple): Feature type {(2, 1), (1, 2), (3, 1), (2, 2)}.
        position (tuple): (row, col) position of the feature's top left corner.
        size (tuple): Feature's (height, width)

    Attributes:
        feat_type (tuple): Feature type.
        position (tuple): Feature's top left corner.
        size (tuple): Feature's width and height.
    """

    def __init__(self, feat_type, position, size):
        self.feat_type = feat_type
        self.position = position
        self.size = size

    def _create_two_horizontal_feature(self, shape):
        """Create a feature of type (2, 1).

        Use int division to obtain half the height.

        Args:
            shape (tuple):  Array numpy-style shape (rows, cols).

        Returns:
            numpy.array: Image containing a Haar feature. (uint8).
        """
        sh = self.size[0] // 2
        y, x = self.position
        height, width = self.size
        haar_image = np.zeros(shape)
        haar_image[y:(y + sh), x:(x + width)] = 255
        haar_image[(y + sh):(y + height), x:(x + width)] = 126

        return haar_image

    def _create_two_vertical_feature(self, shape):
        """Create a feature of type (1, 2).

        Use int division to obtain half the width.

        Args:
            shape (tuple):  Array numpy-style shape (rows, cols).

        Returns:
            numpy.array: Image containing a Haar feature. (uint8).
        """
        sw = self.size[1] // 2
        y, x = self.position
        height, width = self.size
        haar_image = np.zeros(shape)
        haar_image[y:(y + height), x:(x + sw)] = 255
        haar_image[y:(y + height), (x + sw):(x + width)] = 126

        return haar_image

    def _create_three_horizontal_feature(self, shape):
        """Create a feature of type (3, 1).

        Use int division to obtain a third of the height.

        Args:
            shape (tuple):  Array numpy-style shape (rows, cols).

        Returns:
            numpy.array: Image containing a Haar feature. (uint8).
        """
        sh = self.size[0] // 3
        y, x = self.position
        height, width = self.size
        haar_image = np.zeros(shape)
        haar_image[y:(y + sh), x:(x + width)] = 255
        haar_image[(y + sh):(y + sh + sh), x:(x + width)] = 126
        haar_image[(y + sh + sh):(y + height), x:(x + width)] = 255

        return haar_image

    def _create_three_vertical_feature(self, shape):
        """Create a feature of type (1, 3).

        Use int division to obtain a third of the width.

        Args:
            shape (tuple):  Array numpy-style shape (rows, cols).

        Returns:
            numpy.array: Image containing a Haar feature. (uint8).
        """
        sw = self.size[1] // 3
        y, x = self.position
        height, width = self.size
        haar_image = np.zeros(shape)
        haar_image[y:(y + height), x:(x + sw)] = 255
        haar_image[y:(y + height), (x + sw):(x + sw + sw)] = 126
        haar_image[y:(y + height), (x + sw + sw):(x + width)] = 255

        return haar_image

    def _create_four_square_feature(self, shape):
        """Create a feature of type (2, 2).

        Use int division to obtain half the width and half the height.

        Args:
            shape (tuple):  Array numpy-style shape (rows, cols).

        Returns:
            numpy.array: Image containing a Haar feature. (uint8).
        """
        sw = self.size[1] // 2
        sh = self.size[0] // 2
        y, x = self.position
        height, width = self.size
        haar_image = np.zeros(shape)
        haar_image[y:(y + sh), x:(x + sw)] = 126
        haar_image[y:(y + sh), (x + sw):(x + width)] = 255
        haar_image[(y + sh):(y + height), x:(x + sw)] = 255
        haar_image[(y + sh):(y + height), (x + sw):(x + width)] = 126

        return haar_image

    def preview(self, shape=(24, 24), filename=None):
        """Return an image with a Haar-like feature of a given type.

        Function that calls feature drawing methods. Each method should
        create an 2D zeros array. Each feature is made of a white area (255)
        and a gray area (126).

        The drawing methods use the class attributes position and size.
        Keep in mind these are in (row, col) and (height, width) format.

        Args:
            shape (tuple): Array numpy-style shape (rows, cols).
                           Defaults to (24, 24).

        Returns:
            numpy.array: Array containing a Haar feature (float or uint8).
        """

        if self.feat_type == (2, 1):  # two_horizontal
            X = self._create_two_horizontal_feature(shape)

        if self.feat_type == (1, 2):  # two_vertical
            X = self._create_two_vertical_feature(shape)

        if self.feat_type == (3, 1):  # three_horizontal
            X = self._create_three_horizontal_feature(shape)

        if self.feat_type == (1, 3):  # three_vertical
            X = self._create_three_vertical_feature(shape)

        if self.feat_type == (2, 2):  # four_square
            X = self._create_four_square_feature(shape)

        cv2.imwrite("{}.png".format(filename), X)

        return X

    def evaluate(self, ii):
        """Evaluates a feature's score on a given integral image.

        Calculate the score of a feature defined by the self.feat_type.
        Using the integral image and the sum / subtraction of rectangles to
        obtain a feature's value. Add the feature's white area value and
        subtract the gray area.

        For example, on a feature of type (2, 1):
        score = sum of pixels in the white area - sum of pixels in the gray area

        Keep in mind you will need to use the rectangle sum / subtraction
        method and not numpy.sum(). This will make this process faster and
        will be useful in the ViolaJones algorithm.

        Args:
            ii (numpy.array): Integral Image.

        Returns:
            float: Score value.
        """
        ii = ii.astype(np.float32)
        y, x = self.position
        height, width = self.size

        if self.feat_type == (2, 1):
            sh = self.size[0] // 2

            A = ii[y - 1][x - 1]
            B = ii[y - 1][x + width - 1]
            C = ii[y + sh - 1][x - 1]
            D = ii[y + sh - 1][x + width- 1]
            E = ii[y + height - 1][x - 1]
            F = ii[y + height - 1][x + width - 1]

            sum1 = A + D - B - C
            sum2 = C + F - E - D

            return sum1 - sum2

        elif self.feat_type == (1, 2):
            sw = self.size[1] // 2

            A = ii[y - 1][x - 1]
            B = ii[y - 1][x + sw - 1]
            C = ii[y + height - 1][x - 1]
            D = ii[y + height - 1][x + sw - 1]
            E = ii[y - 1][x + width - 1]
            F = ii[y + height - 1][x + width - 1]

            sum1 = A + D - B - C
            sum2 = B + F - E - D

            return sum1 - sum2

        elif self.feat_type == (3, 1):
            sh = self.size[0] // 3

            A = ii[y - 1][x - 1]
            B = ii[y - 1][x + width - 1]
            C = ii[y + sh - 1][x - 1]
            D = ii[y + sh - 1][x + width - 1]
            E = ii[y + sh + sh - 1][x - 1]
            F = ii[y + sh + sh - 1][x + width - 1]
            G = ii[y + height - 1][x - 1]
            H = ii[y + height - 1][x + width - 1]

            sum1 = A + D - B - C
            sum2 = C + F - E - D
            sum3 = E + H - F - G

            return sum1 - sum2 + sum3

        elif self.feat_type == (1, 3):
            sw = self.size[1] // 3

            A = ii[y - 1][x - 1]
            B = ii[y - 1][x + sw - 1]
            C = ii[y + height - 1][x - 1]
            D = ii[y + height - 1][x + sw - 1]
            E = ii[y - 1][x + sw + sw - 1]
            F = ii[y + height - 1][x + sw + sw - 1]
            G = ii[y - 1][x + width - 1]
            H = ii[y + height - 1][x + width - 1]

            sum1 = A + D - B - C
            sum2 = B + F - E - D
            sum3 = E + H - G - F

            return sum1 - sum2 + sum3

        elif self.feat_type == (2, 2):
            sw = self.size[1] // 2
            sh = self.size[0] // 2

            A = ii[y - 1][x - 1]
            B = ii[y - 1][x + sw - 1]
            C = ii[y + sh - 1][x - 1]
            D = ii[y + sh - 1][x + sw - 1]
            E = ii[y - 1][x + width - 1]
            F = ii[y + sh - 1][x + width - 1]
            G = ii[y + height - 1][x - 1]
            H = ii[y + height - 1][x + sw - 1]
            I = ii[y + height - 1][x + width - 1]

            sum1 = A + D - B - C
            sum2 = B + F - E - D
            sum3 = C + H - D - G
            sum4 = D + I - F - H

            return sum2 + sum3 - sum1 - sum4

        else:
            raise NotImplementedError


def convert_images_to_integral_images(images):
    """Convert a list of grayscale images to integral images.

    Args:
        images (list): List of grayscale images (uint8 or float).

    Returns:
        (list): List of integral images.
    """
    integrals = []
    dim, height, width = np.shape(images)
    for n in range(dim):
        intagral = np.zeros(shape=(height, width))
        for y in range(height):
            for x in range(width):
                intagral[y, x] = np.sum(images[n][:(y + 1), :(x + 1)])
        integrals.append(intagral)

    return integrals


class ViolaJones:
    """Viola Jones face detection method

    Args:
        pos (list): List of positive images.
        neg (list): List of negative images.
        integral_images (list): List of integral images.

    Attributes:
        haarFeatures (list): List of haarFeature objects.
        integralImages (list): List of integral images.
        classifiers (list): List of weak classifiers (VJ_Classifier).
        alphas (list): Alpha values, one for each weak classifier.
        posImages (list): List of positive images.
        negImages (list): List of negative images.
        labels (numpy.array): Positive and negative labels.
    """
    def __init__(self, pos, neg, integral_images):
        self.haarFeatures = []
        self.integralImages = integral_images
        self.classifiers = []
        self.alphas = []
        self.posImages = pos
        self.negImages = neg
        self.labels = np.hstack((np.ones(len(pos)), -1*np.ones(len(neg))))

    def createHaarFeatures(self):
        # Let's take detector resolution of 24x24 like in the paper
        FeatureTypes = {"two_horizontal": (2, 1),
                        "two_vertical": (1, 2),
                        "three_horizontal": (3, 1),
                        "three_vertical": (1, 3),
                        "four_square": (2, 2)}

        haarFeatures = []
        for _, feat_type in FeatureTypes.items():
            for sizei in range(feat_type[0], 24 + 1, feat_type[0]):
                for sizej in range(feat_type[1], 24 + 1, feat_type[1]):
                    for posi in range(0, 24 - sizei + 1, 4):
                        for posj in range(0, 24 - sizej + 1, 4):
                            haarFeatures.append(
                                HaarFeature(feat_type, [posi, posj],
                                            [sizei-1, sizej-1]))
        self.haarFeatures = haarFeatures

    def train(self, num_classifiers):

        # Use this scores array to train a weak classifier using VJ_Classifier
        # in the for loop below.
        scores = np.zeros((len(self.integralImages), len(self.haarFeatures)))
        print(" -- compute all scores --")
        for i, im in enumerate(self.integralImages):
            scores[i, :] = [hf.evaluate(im) for hf in self.haarFeatures]

        weights_pos = np.ones(len(self.posImages), dtype='float') * 1.0 / (
                           2*len(self.posImages))
        weights_neg = np.ones(len(self.negImages), dtype='float') * 1.0 / (
                           2*len(self.negImages))
        weights = np.hstack((weights_pos, weights_neg))

        print(" -- select classifiers --")
        for i in range(num_classifiers):
            # Step 1: Normalize the weights
            weights_total = np.sum(weights)
            weights = weights / weights_total

            # Step 2: Training the VJ_Classifier
            vjc = VJ_Classifier(scores, self.labels, weights, thresh=0, feat=0, polarity=1)
            vjc.train()
            error = vjc.error

            # Step 3: Append coefficients to classifier
            self.classifiers.append(vjc)

            # Step 4: Update the weights
            beta = float(error) / (1. - error)
            for i in range(len(self.integralImages)):
                if self.labels[i] == vjc.predict(scores[i]):
                    weights[i] = weights[i] * beta
                else:
                    weights[i] = weights[i]

            # Step 5: Calculate alphas
            self.alphas.append(np.log(1. / beta))

    def predict(self, images):
        """Return predictions for a given list of images.

        Args:
            images (list of element of type numpy.array): list of images (observations).

        Returns:
            list: Predictions, one for each element in images.
        """

        ii = convert_images_to_integral_images(images)

        scores = np.zeros((len(ii), len(self.haarFeatures)))

        # Populate the score location for each classifier 'clf' in
        # self.classifiers.

        # Obtain the Haar feature id from clf.feature

        # Use this id to select the respective feature object from
        # self.haarFeatures

        # Add the score value to score[x, feature id] calling the feature's
        # evaluate function. 'x' is each image in 'ii'
        for i, x in enumerate(ii):
            for clf in self.classifiers:
                feature_ind = clf.feature
                feature_haar = self.haarFeatures[feature_ind]
                scores[i, feature_ind] = feature_haar.evaluate(x)

        result = []

        # Append the results for each row in 'scores'. This value is obtained
        # using the equation for the strong classifier H(x).
        for x in scores:
            alphas_total = np.sum(self.alphas)
            predictions_total = 0.
            for j in range(len(self.classifiers)):
                predictions_total += self.alphas[j] * self.classifiers[j].predict(x)

            res = 1 if predictions_total >= (alphas_total * 0.5) else -1
            result.append(res)

        return result

    def faceDetection(self, image, filename):
        """Scans for faces in a given image.

        Complete this function following the instructions in the problem set
        document.

        Use this function to also save the output image.

        Args:
            image (numpy.array): Input image.
            filename (str): Output image file name.

        Returns:
            None.
        """
        img_temp = np.copy(image)
        img_gray = cv2.cvtColor(img_temp, cv2.COLOR_BGR2GRAY)

        height, width = np.shape(img_gray)
        rect_d, tl, br = 24, [], []

        windows = []
        for i in range(height - rect_d):
            for j in range(width - rect_d):
                window = np.zeros((rect_d, rect_d))
                tl.append([j, i])
                br.append([j + rect_d, i + rect_d])
                window[:, :] = img_gray[i:(i + rect_d), j:(j + rect_d)]
                windows.append(window)

        predictions = self.predict(windows)

        pos_tl, pos_br = [], []
        for i, prediction in enumerate(predictions):
            if prediction == 1:
                pos_tl.append(tl[i])
                pos_br.append(br[i])

        pos_tl, pos_br = np.asarray(pos_tl), np.asarray(pos_br)
        ave_tl, ave_br = np.mean(pos_tl, axis=0).astype(int) + (5, 0), np.mean(pos_br, axis=0).astype(int) + (5, 0)

        cv2.rectangle(img_temp, tuple(ave_tl), tuple(ave_br), (0, 0, 255), 2)
        cv2.imwrite("{}.png".format(filename), img_temp)
