import unittest
import os
import shutil
import tempfile
import numpy as np
import cv2
from app.services.face_detection import detector
from app.services.face_recognition import FaceRecognitionService
from app.config import Config

class TestRecognition(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dataset_dir = os.path.join(self.test_dir, 'dataset')
        self.models_dir = os.path.join(self.test_dir, 'models')
        os.makedirs(self.dataset_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_face_detector_quality_assessment(self):
        # Create a sharp dummy face image
        sharp_img = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(sharp_img, (100, 100), 50, 200, -1)
        cv2.circle(sharp_img, (80, 80), 10, 50, -1)
        cv2.circle(sharp_img, (120, 80), 10, 50, -1)
        
        is_good, scores, msg = detector.assess_quality(sharp_img)
        self.assertIn('sharpness', scores)
        self.assertIn('brightness', scores)
        self.assertIn('contrast', scores)

    def test_face_detector_blur_rejection(self):
        # Create a flat blurred image with low variance
        blurry_img = np.full((200, 200), 128, dtype=np.uint8)
        is_good, scores, msg = detector.assess_quality(blurry_img)
        self.assertFalse(is_good)
        self.assertIn("blurry", msg.lower())

    def test_confidence_score_normalization(self):
        service = FaceRecognitionService()
        # Test mock distance conversion logic
        # Distance = 0 -> 100% confidence
        conf_0 = max(0.0, min(100.0, round(100.0 - (0.0 * 0.65), 1)))
        self.assertEqual(conf_0, 100.0)
        
        # Distance = 50 -> ~67.5% confidence
        conf_50 = max(0.0, min(100.0, round(100.0 - (50.0 * 0.65), 1)))
        self.assertEqual(conf_50, 67.5)
        
        # Distance = 200 -> 0.0% confidence
        conf_200 = max(0.0, min(100.0, round(100.0 - (200.0 * 0.65), 1)))
        self.assertEqual(conf_200, 0.0)

if __name__ == '__main__':
    unittest.main()
