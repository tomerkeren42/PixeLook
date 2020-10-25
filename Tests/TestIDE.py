import random
import time

from Tests.TestUtils import *


class Test_Manager:
    def __init__(self, gaze_manager):
        self.pixel_real = np.zeros(2)
        self.pixel_linear = np.zeros(2)
        self.pixel_linear_fixed = np.zeros(2)
        self.pixel_trig = np.zeros(2)
        self.pixel_trig_fixed = np.zeros(2)

        self.gaze_manager = gaze_manager
        self.width = gaze_manager.width_px
        self.height = gaze_manager.height_px
        self.person_name = gaze_manager.user_name
        self.model_method = gaze_manager.model_method

        self.iteration = 0
        self.test_csv = new_csv_session("OurDB")

        self.debug_total_error_linear =0
        self.debug_total_improve_linear = 0
        self.debug_total_error_trig = 0
        self.debug_total_improve_trig = 0

        self.start_time_iteration = 0

    def self_check(self):
        self.gaze_manager.gui.print_pixel(self.gaze_manager.get_cur_pixel())
        # un-comment if you want to wait for mouse-clicks to capture
        # self.gaze_manager.gui.wait_key()

    def not_valid_pixel(self):
        log_error(self.test_csv, "pixel")
        self.gaze_manager.gui.button.config(text="pixel was out of bounds! Click to continue")
        self.gaze_manager.gui.wait_key()
        self.gaze_manager.gui.button.config(text=text_for_capture)
        self.iteration -= 1

    def not_valid_detect(self):
        log_error(self.test_csv, "detect")
        self.gaze_manager.gui.button.config(text="Re-center your face to the camera! Click only when ready")
        self.gaze_manager.gui.wait_key()
        self.gaze_manager.gui.button.config(text=text_for_capture)
        self.iteration -= 1

    def new_log_input(self, cur_smp, method):
        if method == "Trig":
            err_before_net = compute_error_mm(self.pixel_real, self.pixel_trig, self.gaze_manager.pixel_per_mm)
            err_after_net = compute_error_mm(self.pixel_real, self.pixel_trig_fixed, self.gaze_manager.pixel_per_mm)
            self.debug_total_error_trig += err_after_net[0]
            cur_smp.improve = err_before_net[0] - err_after_net[0]
            self.debug_total_improve_trig += cur_smp.improve
            cur_smp.set_from_session(self.pixel_real, self.pixel_trig_fixed, self.gaze_manager.screen_size,
                                     self.gaze_manager.last_distance, self.person_name,
                                     "Trigonometric", self.model_method, err_after_net)
            log_sample_csv(cur_smp, self.test_csv)

        elif method == "Linear":
            err_before_net = compute_error_mm(self.pixel_real, self.pixel_linear, self.gaze_manager.pixel_per_mm)
            err_after_net = compute_error_mm(self.pixel_real, self.pixel_linear_fixed, self.gaze_manager.pixel_per_mm)
            self.debug_total_error_linear += err_after_net[0]
            cur_smp.improve = err_before_net[0] - err_after_net[0]
            self.debug_total_improve_linear += cur_smp.improve
            cur_smp.set_from_session(self.pixel_real, self.pixel_linear_fixed, self.gaze_manager.screen_size,
                                     self.gaze_manager.last_distance, self.person_name,
                                     "Linear", self.model_method, err_after_net)
            log_sample_csv(cur_smp, self.test_csv)

    def draw_target(self):
        self.pixel_real = [random.randint(0, self.width-10), random.randint(0, self.height-10)]
        # self.gaze_manager.gui.print_pixel(self.pixel_real)
        self.gaze_manager.gui.move_button_to_pixel(self.pixel_real)
        # wanted the button to move with the tag, but it's not working atm
        # self.gaze_manager.gui.print_capture_button(self.tag)

    def capture(self):
        self.gaze_manager.gui.wait_key()
        self.start_time_iteration = time.perf_counter()
        # time measurement
        start_time = time.perf_counter()
        self.pixel_linear, self.pixel_trig = self.gaze_manager.get_cur_pixel()
        # print(time.perf_counter() - start_time)
        # print("9. get cur pixel took: ", (time.perf_counter() - start_time))

        return self.pixel_linear, self.pixel_trig

    def get_pixel_with_method(self, kind="Trig", net=True):
        pixel_linear, pixel_trig = self.capture()
        if kind == "Trig":
            if net:
                return self.gaze_manager.trig_fix_sys.use_net(pixel_trig)
            else:
                return pixel_trig
        else:
            if net:
                return self.gaze_manager.linear_fix_sys.use_net(self.pixel_linear)
            else:
                return pixel_linear

    def collect(self):
        for self.iteration in range(num_pics_per_session):
            cur_smp = Sample()
            self.draw_target()
            is_valid_pixel = self.capture()
            # TODO : check for both linear and trig pixels
            start_time = time.perf_counter()
            if is_valid_pixel[1] is not error_in_detect or is_valid_pixel[0] is not error_in_detect:
                self.pixel_trig_fixed = self.gaze_manager.trig_fix_sys.use_net(self.pixel_trig)
                # print(time.perf_counter() - start_time)
                # print("10. trig fix net took: ", time.perf_counter() - start_time)
                start_time = time.perf_counter()
                self.pixel_linear_fixed = self.gaze_manager.linear_fix_sys.use_net(self.pixel_linear)
                # print(time.perf_counter() - start_time)
                # print("11. linear fix net took: ", time.perf_counter() - start_time)
                self.new_log_input(cur_smp, "Trig")
                self.new_log_input(cur_smp, "Linear")

                # self.gaze_manager.gui.print_pixel(self.pixel_trig, "black")
                # self.gaze_manager.gui.print_pixel(self.pixel_trig_fixed, "blue")
                # self.gaze_manager.gui.print_pixel(self.pixel_linear, "yellow")
                # self.gaze_manager.gui.print_pixel(self.pixel_linear_fixed, "green")
                # self.gaze_manager.gui.wait_key()

                self.gaze_manager.gui.w.delete("all")
            # not valid
            else:
                self.not_valid_detect()
            # print(time.perf_counter() - self.start_time_iteration)
            # print("12. entire iteration from click to next compute took: ", time.perf_counter() - self.start_time_iteration)
        self.finish_test()

    def finish_test(self):
        average_error_linear = self.debug_total_error_linear/num_pics_per_session
        average_error_trig = self.debug_total_error_trig/num_pics_per_session
        average_improve_linear = self.debug_total_improve_linear/num_pics_per_session
        average_improve_trig = self.debug_total_improve_trig/num_pics_per_session

        print(f"final stats: \n average error linear is: {average_error_linear} \n average improve linear is: {average_improve_linear} \naverage error trig is: {average_error_trig} \n average improve trig is: {average_improve_trig}")
        self.test_csv.close()
