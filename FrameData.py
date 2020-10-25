import UtilsAndModels.utils as utils
from UtilsAndModels.Defines import *
import time

class FrameData:
    def __init__(self, img, is_debug=True):
        self.orig_img = img
        self.debug_img = img
        self.is_face = False
        self.landmarks_6 = 0
        self.landmarks_all = 0
        self.relevant_locations = [36, 39, 42, 45, 48, 54]
        self.rotation_vector = np.zeros(3)
        self.translation_vector = np.zeros(3)
        self.is_debug = is_debug
        self.gaze_origin = 0
        self.net_input = 0
        self.img_for_net = 0
        self.head_pose_for_net = 0

    def flip(self):
        self.debug_img = cv2.flip(self.debug_img, 1)

    def get_landmarks(self, shape, specific_locations=False):
        if specific_locations:
            num = len(self.relevant_locations)
            list = self.relevant_locations
        else:
            num = 68
            list = range(num)
        coords = np.zeros((num, 2), dtype="float32")
        j = 0
        for i in list:
            coords[j] = (shape.part(i).x, shape.part(i).y)
            j = j + 1
        return coords

    def face_landmark_detect(self, head_loc=None):
        if head_loc is not None:
            return True
        gray = cv2.cvtColor(self.orig_img, cv2.COLOR_BGR2GRAY)

        # dlib face detector
        # rects_dlib = detector(gray, 0)

        # cv2 face detector
        start_time = time.perf_counter()
        rects_cv = face_cascade.detectMultiScale(gray)
        # print(time.perf_counter() - start_time)
        # print("1. detect face took: ", time.perf_counter()-start_time)
        #  scaleFactor=1.1,
        if np.size(rects_cv) > 0:
            rects_cv_to_dlib = dlib.rectangle(rects_cv[0][0], rects_cv[0][1], rects_cv[0][0] + rects_cv[0][2],
                                              rects_cv[0][1] + rects_cv[0][3])
            start_time = time.perf_counter()
            prediction = predictor(gray, rects_cv_to_dlib)
            # print(time.perf_counter() - start_time)
            # print("2. predict face landmarks took: ", time.perf_counter()-start_time)
            self.landmarks_all = self.get_landmarks(prediction, False)
            self.landmarks_6 = self.landmarks_all[self.relevant_locations]
            self.is_face = True
        return self.is_face

    def head_pose_detect(self, head_loc=None):
        if head_loc is None:
            landmarks = self.landmarks_6
        else:
            landmarks = head_loc
        mini_face_model_adj = LANDMARKS_6_PNP.T.reshape(LANDMARKS_6_PNP.shape[1], 1, 3)
        dist_coeffs = utils.global_camera_coeffs
        camera_matrix = utils.global_camera_matrix
        start_time = time.perf_counter()
        (success, self.rotation_vector, self.translation_vector) = cv2.solvePnP(mini_face_model_adj, landmarks,
                                                                                camera_matrix,
                                                                                dist_coeffs,
                                                                                True)

        (success, self.rotation_vector, self.translation_vector) = cv2.solvePnP(mini_face_model_adj, landmarks,
                                                                                camera_matrix,
                                                                                dist_coeffs, self.rotation_vector,
                                                                                self.translation_vector,
                                                                                True)
        # print(time.perf_counter() - start_time)
        # print("3. head pose detect took: ", time.perf_counter()- start_time)
