import unittest
import numpy as np
from gaze_predictor import GazePredictor
# import tensorflow as tf
import cv2

class TestGazePredictor(unittest.TestCase):
    def setUp(self):
        self.gaze_predictor = GazePredictor('./eye_gaze_v31_20.h5', './adjustment_model.pkl', './shape_predictor_68_face_landmarks.dat')

    def test_predict_gaze(self):
        dummy_frame_path = "eloise_0b8aa6d2-364c-4913-8e51-bc2ca0e5a43a.png"
        dummy_frame = cv2.imread(dummy_frame_path)
        gaze_x_scaled, gaze_y_scaled, adjusted_x, adjusted_y = self.gaze_predictor.predict_gaze(dummy_frame)
        print(f"gaze_x_scaled: {gaze_x_scaled}")
        print(f"gaze_y_scaled: {gaze_y_scaled}")
        print(f"adjusted_x: {adjusted_x}")
        print(f"adjusted_y: {adjusted_y}")
        self.assertIsNotNone(gaze_x_scaled)
        self.assertIsNotNone(gaze_y_scaled)
        self.assertIsNotNone(adjusted_x)
        self.assertIsNotNone(adjusted_y)

if __name__ == '__main__':
    unittest.main()