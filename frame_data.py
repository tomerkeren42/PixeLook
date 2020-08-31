from helpers.utils import *
from HeadPoseBasedSolution.NewImgPreProcess.NormalizeData import *
dist_coeff_a = np.array([0., 0., 0., 0., 0.]).reshape(-1, 1)
# TODO: might want to check this norm matrix, maybe 1600 is not for our resolution?
# TODO: in second look, no one is using it. it's re-defined in camera_matrix
# norm_matrix = np.array([1600., 0., 112.,
#                         0., 1600., 112.,
#                         0., 0., 1.]).reshape(3, 3)
# rvec = np.zeros(3, dtype=np.float)
# tvec = np.array([0, 0, 1], dtype=np.float)


def shape_to_np(shape, dtype="int"):
    # initialize the list of (x, y)-coordinates
    coords = np.zeros((shape.num_parts, 2), dtype=dtype)

    # loop over all facial landmarks and convert them
    # to a 2-tuple of (x, y)-coordinates
    for i in range(0, shape.num_parts):
        coords[i] = (shape.part(i).x, shape.part(i).y)

    # return the list of (x, y)-coordinates
    return coords


class FrameData:
    def __init__(self, img, is_debug=True):
        self.orig_img = img
        self.debug_img = img
        self.is_face = False
        self.shape = 0
        self.rect = 0
        self.rotation_vector = np.zeros(3)
        self.translation_vector = np.zeros(3)
        self.is_debug = is_debug
        self.gaze_origin = 0
        self.camera_matrix = np.array([960., 0., 640., 0., 960., 360., 0., 0., 1.]).reshape(3, 3)
        self.net_input = 0

    def get_head_pose(self):
        return self.head_pose

    def get_eye_img(self):
        return self.r_eye_img

    def flip(self):
        self.debug_img = cv2.flip(self.debug_img, 1)

    def face_landmark_detect(self):
        gray = cv2.cvtColor(self.orig_img, cv2.COLOR_BGR2GRAY)
        rects = detector(gray, 0)
        if np.size(rects) > 0:
            shape = predictor(gray, rects[0])
            shape = shape_to_np(shape)
            self.is_face = True
            self.shape = shape
            self.rect = rects[0]
        return self.is_face

    def eyes_detect(self):
        self.r_eye, self.l_eye = eye_detector(self.orig_img, self.shape)

    def head_pose_detect(self):
        landmarks = np.array(self.shape, dtype="double")
        # check for distortion
        dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion
        (success, self.rotation_vector, self.translation_vector) = cv2.solvePnP(face_model, landmarks, self.camera_matrix,
                                                                                dist_coeffs, flags=cv2.SOLVEPNP_EPNP)
        (success, self.rotation_vector, self.translation_vector) = cv2.solvePnP(face_model, landmarks, self.camera_matrix,
                                                                                dist_coeffs, self.rotation_vector,
                                                                                self.translation_vector, True)
        # Project a 3D point (0, 0, 1000.0) onto the image plane.
        # (nose_end_point2D, jacobian) = cv2.projectPoints(np.array([(0.0, 0.0, 1000.0)]), self.rotation_vector,
        #                                                  self.translation_vector, camera_matrix, dist_coeffs)
        #
        # p1 = (int(image_points[NOSE_INDEX][0]), int(image_points[NOSE_INDEX][1]))
        # p2 = (int(nose_end_point2D[0][0][0]), int(nose_end_point2D[0][0][1]))
        # if self.is_debug:
        #     cv2.line(self.debug_img, p1, p2, (255, 0, 0), 2)
        # rot = Rotation.from_rotvec(self.rotation_vector)
        # model3d = camera_matrix_a @ self.rotation_vector.T + self.translation_vector
        # self.angles = rot.as_euler('XYZ')[:2] * np.array([1, -1])

    def pre_proccess_for_net(self):
        # img = self.orig_img
        # face = face model
        # hr, ht = self.rotation_vector, self.translation_vector
        # camera matrix

        # TODO: need to get face as they use it - six points from generic face model..
        face = face_model

        self.net_input = normalizeData(self.orig_img, face, self.rotation_vector,
                             self.translation_vector, self.camera_matrix)

        # show results of right eye image
        label = self.net_input[0][1]
        print('The label is: ', label)
        # convert label to euler angle
        gaze_theta = np.arcsin((-1) * label[1])
        gaze_phi = np.arctan2((-1) * label[0], (-1) * label[2])

        # show normalized image
        img_normalized = self.net_input[0][0]
        cv2.imshow('image', img_normalized)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

