import dlib
import numpy as np
import pickle
from collections import deque
from keras.models import load_model
import cv2
#improt to get the screen dimensions
import pyautogui as pag
class GazePredictor:
    def __init__(self, model_path, adjustment_model_path, shape_predictor_path, screen_dimensions=(pag.size()[0], pag.size()[1])):
        self.screen_width, self.screen_height = screen_dimensions
        self.global_detector = dlib.get_frontal_face_detector()
        self.global_predictor = dlib.shape_predictor(shape_predictor_path)
        self.model = self.load_keras_model(model_path)
        self.adjustment_model = self.load_pickle_model(adjustment_model_path)
        self.gaze_points_queue = deque(maxlen=5)
        self.adjusted_gaze_points_queue = deque(maxlen=5)

    def load_keras_model(self, model_path):
        return load_model(model_path)

    def load_pickle_model(self, model_path):
        with open(model_path, 'rb') as f:
            return pickle.load(f)
        
    def extract_eye_region(self, image, landmarks, left_eye_points, right_eye_points, nose_bridge_points, forehead_points):
        # Combine the eye, nose bridge, and forehead points
        eye_points = left_eye_points + right_eye_points
        all_points = eye_points + nose_bridge_points + forehead_points

        # Extract the coordinates of the combined points
        region = np.array([(landmarks.part(point).x, landmarks.part(point).y) for point in all_points])

        # Find the bounding box coordinates
        min_x = np.min(region[:, 0])
        max_x = np.max(region[:, 0])
        min_y = np.min(region[:, 1])
        max_y = np.max(region[:, 1])

        # Crop the region to create a rectangle
        cropped_region = image[min_y:max_y, min_x:max_x]

        return cropped_region, (min_x, min_y, max_x, max_y)
        
    def get_combined_eyes(self, frame, global_detector, global_predictor, target_size=(200, 100)):
        """
        Detects, enhances, and combines the eye regions including the nose bridge from the frame.
        Args:
            frame: The input image frame.
            global_detector: Face detector.
            global_predictor: Landmark predictor.
            target_size: Target size for resizing the combined eye region.
        Returns:
            The combined eye regions including the nose bridge, or None if not detected.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = global_detector(gray)

        # super resolution image
        for face in faces:
            landmarks = global_predictor(gray, face)

            forehead_points = [20, 21, 22, 23, 0 ,16]
            left_eye_landmarks = [36, 37, 38, 39, 40, 41]
            right_eye_landmarks = [42, 43, 44, 45, 46, 47]
            nose_bridge_points = [27, 28, 29]

            combined_eye_region, _ = self.extract_eye_region(
                frame, landmarks, left_eye_landmarks, right_eye_landmarks, nose_bridge_points, forehead_points)

            if isinstance(combined_eye_region, np.ndarray) and combined_eye_region.size > 0:
                # Resize to the final target size
                combined_eye_final_resized = cv2.resize(combined_eye_region, target_size, interpolation=cv2.INTER_AREA)
                combined_eye_final_resized = combined_eye_final_resized.astype(np.float32) / 255.0
                return combined_eye_final_resized
            else:
                # Handle the case where combined_eye_region is empty or not valid
                return None
        return None

    def predict_gaze(self, frame):
        combined_eyes = self.get_combined_eyes(frame, self.global_detector, self.global_predictor)
        if combined_eyes is not None:
            combined_eyes = np.expand_dims(combined_eyes, axis=0)
            predicted_gaze = self.model.predict(combined_eyes)[0][0]

            # Correctly access the elements of predicted_gaze[0]
            gaze_x_scaled = int(predicted_gaze[0] * self.screen_width)  # Access the first element for x
            gaze_y_scaled = int(predicted_gaze[1] * self.screen_height)  # Access the second element for y

            # Adjust gaze prediction
            adjusted_pred = self.adjustment_model.predict(predicted_gaze.reshape(1, -1))[0]
            adjusted_x, adjusted_y = int(adjusted_pred[0] * self.screen_width), int(adjusted_pred[1] * self.screen_height)

            return gaze_x_scaled, gaze_y_scaled, adjusted_x, adjusted_y
        else:
            return None, None, None, None
        
    def moving_average(self, new_point, queue):
        queue.append(new_point)
        return [sum(x) / len(queue) for x in zip(*queue)]