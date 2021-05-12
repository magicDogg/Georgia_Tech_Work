"""
CS6476 Problem Set 5 imports. Only Numpy and cv2 are allowed.
"""
import numpy as np
import cv2


# Assignment code
class KalmanFilter(object):
    """A Kalman filter tracker"""

    def __init__(self, init_x, init_y, Q=0.1 * np.eye(4), R=0.1 * np.eye(2)):
        """Initializes the Kalman Filter

        Args:
            init_x (int or float): Initial x position.
            init_y (int or float): Initial y position.
            Q (numpy.array): Process noise array.
            R (numpy.array): Measurement noise array.
        """
        self.state = np.array([init_x, init_y, 0., 0.])
        self.Q, self.R = Q, R
        self.D = [[1., 0., 1., 0.],
                  [0., 1., 0., 1.],
                  [0., 0., 1., 0.],
                  [0., 0., 0., 1.]]
        self.M = [[1., 0., 0., 0.],
                  [0., 1., 0., 0.]]
        self.K = [[0., 0., 0., 0.],
                  [0., 0., 0., 0.]]
        self.P = [[0., 0., 0., 0.],
                  [0., 0., 0., 0.],
                  [0., 0., 0., 0.],
                  [0., 0., 0., 0.]]
        self.y = np.ndarray([init_x, init_y])

    def predict(self):
        self.state = np.dot(self.state, self.D)
        self.P = np.dot(self.D, np.dot(self.P, np.transpose(self.D))) + self.Q

    def correct(self, meas_x, meas_y):
        self.K = np.dot(np.dot(self.P, np.transpose(self.M)),
                        np.linalg.inv(np.dot(np.dot(self.M, self.P), np.transpose(self.M)) + self.R))
        self.y = np.array([meas_x, meas_y])
        self.state = self.state + np.dot((self.y - np.dot(self.state, np.transpose(self.M))), np.transpose(self.K))
        self.P = self.P - np.dot(np.dot(self.K, self.M), self.P)

    def process(self, measurement_x, measurement_y):
        self.predict()
        self.correct(measurement_x, measurement_y)

        state = (self.state[0], self.state[1])

        return state


class ParticleFilter(object):
    """A particle filter tracker.

    Encapsulating state, initialization and update methods. Refer to
    the method run_particle_filter( ) in experiment.py to understand
    how this class and methods work.
    """

    def __init__(self, frame, template, **kwargs):
        """Initializes the particle filter object.

        The main components of your particle filter should at least be:
        - self.particles (numpy.array): Here you will store your particles.
                                        This should be a N x 2 array where
                                        N = self.num_particles. This component
                                        is used by the autograder so make sure
                                        you define it appropriately.
                                        Make sure you use (x, y)
        - self.weights (numpy.array): Array of N weights, one for each
                                      particle.
                                      Hint: initialize them with a uniform
                                      normalized distribution (equal weight for
                                      each one). Required by the autograder.
        - self.template (numpy.array): Cropped section of the first video
                                       frame that will be used as the template
                                       to track.
        - self.frame (numpy.array): Current image frame.

        Args:
            frame (numpy.array): color BGR uint8 image of initial video frame,
                                 values in [0, 255].
            template (numpy.array): color BGR uint8 image of patch to track,
                                    values in [0, 255].
            kwargs: keyword arguments needed by particle filter model:
                    - num_particles (int): number of particles.
                    - sigma_exp (float): sigma value used in the similarity
                                         measure.
                    - sigma_dyn (float): sigma value that can be used when
                                         adding gaussian noise to u and v.
                    - template_rect (dict): Template coordinates with x, y,
                                            width, and height values.
        """
        self.num_particles = kwargs.get('num_particles')  # required by the autograder
        self.sigma_exp = kwargs.get('sigma_exp')  # required by the autograder
        self.sigma_dyn = kwargs.get('sigma_dyn')  # required by the autograder
        self.template_rect = kwargs.get('template_coords')  # required by the autograder

        # If you want to add more parameters, make sure you set a default value so that
        # your test doesn't fail the autograder because of an unknown or None value.
        self.frame, self.template = frame, template
        self.particles = np.zeros((self.num_particles, 2))
        for i in range(self.num_particles):
            self.particles[i] = [self.template_rect['x'] + self.template_rect['w']/2 - 1,
                                 self.template_rect['y'] + self.template_rect['h']/2 - 1]
        self.particles += np.random.normal(0, self.sigma_dyn, self.particles.shape)
        self.weights = np.ones(self.num_particles) * (1 / self.num_particles)

        # Initialize any other components you may need when designing your filter.
        self.state = np.array([0., 0.])
        self.index = np.arange(self.num_particles)

    def get_particles(self):
        """Returns the current particles state.

        This method is used by the autograder. Do not modify this function.

        Returns:
            numpy.array: particles data structure.
        """
        return self.particles

    def get_weights(self):
        """Returns the current particle filter's weights.

        This method is used by the autograder. Do not modify this function.

        Returns:
            numpy.array: weights data structure.
        """
        return self.weights

    def get_error_metric(self, template, frame_cutout):
        """Returns the error metric used based on the similarity measure.

        Returns:
            float: similarity value.
        """
        height, width = template.shape[0], template.shape[1]
        mse = np.sum(np.subtract(template, frame_cutout, dtype=np.float32) ** 2) / float(height * width)
        similarity = np.exp(-mse / (2*(self.sigma_exp ** 2)))

        return similarity

    def resample_particles(self):
        """Returns a new set of particles

        This method does not alter self.particles.

        Use self.num_particles and self.weights to return an array of
        resampled particles based on their weights.

        See np.random.choice or np.random.multinomial.
        
        Returns:
            numpy.array: particles data structure.
        """
        height, width, _ = self.frame.shape
        new_particles = np.zeros_like(self.particles)
        indices = np.random.choice(self.index, self.num_particles, True, p=self.weights)

        for i in range(self.num_particles):
            new_particles[i, :] = self.particles[indices[i], :]

        new_particles[:, 0] = np.clip(new_particles[:, 0], 0, width - 1)
        new_particles[:, 1] = np.clip(new_particles[:, 1], 0, height - 1)

        return new_particles

    def process(self, frame):
        """Processes a video frame (image) and updates the filter's state.

        Implement the particle filter in this method returning None
        (do not include a return call). This function should update the
        particles and weights data structures.

        Make sure your particle filter is able to cover the entire area of the
        image. This means you should address particles that are close to the
        image borders.

        Args:
            frame (numpy.array): color BGR uint8 image of current video frame,
                                 values in [0, 255].

        Returns:
            None.
        """
        self.particles += np.random.normal(0, self.sigma_dyn, self.particles.shape)

        frame_height, frame_width, _ = np.shape(frame)
        template_height, template_width, _ = np.shape(self.template)

        minx = np.clip((self.particles[:, 0] - template_width / 2).astype(np.int), 0, frame_width - template_width - 1)
        miny = np.clip((self.particles[:, 1] - template_height / 2).astype(np.int), 0, frame_height - template_height - 1)
        candidates = []

        for i in range(self.num_particles):
            candidates.append(frame[miny[i]:miny[i] + template_height, minx[i]:minx[i] + template_width, :])

        self.weights = np.array([self.get_error_metric(self.template, candidate) for candidate in candidates])
        self.weights /= np.sum(self.weights)
        self.particles = self.resample_particles()


    def render(self, frame_in):
        """Visualizes current particle filter state.

        This method may not be called for all frames, so don't do any model
        updates here!

        These steps will calculate the weighted mean. The resulting values
        should represent the tracking window center point.

        In order to visualize the tracker's behavior you will need to overlay
        each successive frame with the following elements:

        - Every particle's (x, y) location in the distribution should be
          plotted by drawing a colored dot point on the image. Remember that
          this should be the center of the window, not the corner.
        - Draw the rectangle of the tracking window associated with the
          Bayesian estimate for the current location which is simply the
          weighted mean of the (x, y) of the particles.
        - Finally we need to get some sense of the standard deviation or
          spread of the distribution. First, find the distance of every
          particle to the weighted mean. Next, take the weighted sum of these
          distances and plot a circle centered at the weighted mean with this
          radius.

        This function should work for all particle filters in this problem set.

        Args:
            frame_in (numpy.array): copy of frame to render the state of the
                                    particle filter.
        """
        x_mean, y_mean, dis_weighted_mean = 0, 0, 0

        for i in range(self.num_particles):
            x_mean += self.weights[i] * self.particles[i, 0]
            y_mean += self.weights[i] * self.particles[i, 1]
            cv2.circle(frame_in, (int(self.particles[i, 0]), int(self.particles[i, 1])), 2, (150, 0, 0), -1)

        template_h, template_w, _ = np.shape(self.template)
        cv2.rectangle(frame_in, (int(x_mean) - template_w // 2, int(y_mean) - template_h // 2),
                      (int(x_mean) + template_w // 2, int(y_mean) + template_h // 2), (0, 200, 0), 2)

        for i in range(self.num_particles):
            distance = np.sqrt((self.particles[i, 0] - x_mean) ** 2 + (self.particles[i, 1] - y_mean) ** 2)
            dis_weighted_mean += distance * self.weights[i]

        cv2.circle(frame_in, (int(x_mean), int(y_mean)), int(dis_weighted_mean), (200, 200, 200), 2)

        return frame_in


class AppearanceModelPF(ParticleFilter):
    """A variation of particle filter tracker."""

    def __init__(self, frame, template, **kwargs):
        """Initializes the appearance model particle filter.

        The documentation for this class is the same as the ParticleFilter
        above. There is one element that is added called alpha which is
        explained in the problem set documentation. By calling super(...) all
        the elements used in ParticleFilter will be inherited so you do not
        have to declare them again.
        """

        super(AppearanceModelPF, self).__init__(frame, template, **kwargs)  # call base class constructor

        self.alpha = kwargs.get('alpha')  # required by the autograder

    def update_model(self, frame):
        frame_height, frame_width, _ = np.shape(frame)
        template_height, template_width, _ = np.shape(self.template)

        ind = np.argmax(self.weights)
        x_mean, y_mean = self.particles[ind, :]

        minx = np.clip((x_mean - template_width / 2).astype(np.int), 0, frame_width - template_width - 1)
        miny = np.clip((y_mean - template_height / 2).astype(np.int), 0, frame_height - template_height - 1)

        best_model = np.zeros((template_height, template_width, 3))
        for i in range(3):
            best_model[:, :, i] = frame[miny:miny + template_height, minx:minx + template_width, i]
        #
        # if self.alpha == 0.05:
        self.alpha += 0.35

        self.template = self.alpha * best_model + (1. - self.alpha) * self.template
        self.template = self.template.astype(np.uint8)

    def process(self, frame):
        """Processes a video frame (image) and updates the filter's state.

        This process is also inherited from ParticleFilter. Depending on your
        implementation, you may comment out this function and use helper
        methods that implement the "Appearance Model" procedure.

        Args:
            frame (numpy.array): color BGR uint8 image of current video frame, values in [0, 255].

        Returns:
            None.
        """
        ParticleFilter.process(self, frame)
        self.update_model(frame)


class MDParticleFilter(AppearanceModelPF):
    """A variation of particle filter tracker that incorporates more dynamics."""

    def __init__(self, frame, template, **kwargs):
        """Initializes MD particle filter object.

        The documentation for this class is the same as the ParticleFilter
        above. By calling super(...) all the elements used in ParticleFilter
        will be inherited so you don't have to declare them again.
        """
        super(MDParticleFilter, self).__init__(frame, template, **kwargs)  # call base class constructor
        # If you want to add more parameters, make sure you set a default value so that
        # your test doesn't fail the autograder because of an unknown or None value.
        #
        # The way to do it is:
        # self.some_parameter_name = kwargs.get('parameter_name', default_value)
        self.beta = 0.996
        self.iteration = 0
        self.template_original = template

    def process(self, frame):
        """Processes a video frame (image) and updates the filter's state.

        This process is also inherited from ParticleFilter. Depending on your
        implementation, you may comment out this function and use helper
        methods that implement the "More Dynamics" procedure.

        Args:
            frame (numpy.array): color BGR uint8 image of current video frame,
                                 values in [0, 255].

        Returns:
            None.
        """
        if (120 < self.iteration < 160) or (185 < self.iteration < 230):
            pass
        else:
            ParticleFilter.process(self, frame)

        self.iteration += 1
        ratio = self.beta ** self.iteration
        self.template = cv2.resize(self.template_original, (0, 0), fx=ratio, fy=ratio)
