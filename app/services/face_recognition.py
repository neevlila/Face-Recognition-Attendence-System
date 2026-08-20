import os
import cv2
import json
import numpy as np
import threading
from datetime import datetime
from app.config import Config
from app.database.models import StudentModel, ActivityLogModel

class FaceRecognitionService:
    def __init__(self):
        self.model_path = Config.TRAINER_MODEL_PATH
        self.labels_path = Config.LABELS_MAP_PATH
        self.recognizer = None
        self.labels_map = {} # {str(face_label): {"student_id": ..., "name": ...}}
        self.is_trained = False
        self.last_trained_time = None
        self.training_status = {'status': 'idle', 'progress': 0, 'message': 'Ready'}
        self.lock = threading.Lock()
        
        self._init_recognizer()
        self.load_model()

    def _init_recognizer(self):
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create(
                radius=1,
                neighbors=8,
                grid_x=8,
                grid_y=8
            )
        except AttributeError:
            raise RuntimeError("cv2.face module is not available. Please ensure opencv-contrib-python is installed.")

    def load_model(self):
        """Loads trained LBPH model and label mapping from disk."""
        with self.lock:
            if os.path.exists(self.model_path) and os.path.exists(self.labels_path):
                try:
                    self.recognizer.read(self.model_path)
                    with open(self.labels_path, 'r', encoding='utf-8') as f:
                        self.labels_map = json.load(f)
                    self.is_trained = True
                    mod_time = os.path.getmtime(self.model_path)
                    self.last_trained_time = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
                    return True
                except Exception as e:
                    self.is_trained = False
                    print(f"Error loading face model: {e}")
                    return False
            else:
                self.is_trained = False
                return False

    def clear_model(self):
        """Clears trained model from memory and deletes artifacts from disk."""
        with self.lock:
            if os.path.exists(self.model_path):
                try:
                    os.remove(self.model_path)
                except Exception:
                    pass
            if os.path.exists(self.labels_path):
                try:
                    os.remove(self.labels_path)
                except Exception:
                    pass

            try:
                self.recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
            except AttributeError:
                pass

            self.labels_map = {}
            self.is_trained = False
            self.last_trained_time = None
            self.training_status = {'status': 'idle', 'progress': 0, 'message': 'No trained face models'}

    def train_model(self):
        """
        Gathers face datasets from dataset/ directory, trains LBPH recognizer,
        and saves model + label mappings. Clears model if 0 samples exist.
        """
        with self.lock:
            self.training_status = {'status': 'in_progress', 'progress': 10, 'message': 'Scanning dataset directory...'}
            
        try:
            dataset_dir = Config.DATASET_DIR
            if not os.path.exists(dataset_dir):
                self.clear_model()
                return {'success': True, 'students_count': 0, 'samples_count': 0, 'message': 'No datasets found. Model cleared.'}

            faces = []
            labels = []
            labels_map = {} # {str(label): {'student_id': ..., 'name': ...}}
            
            student_folders = [d for d in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, d))]
            if not student_folders:
                self.clear_model()
                return {'success': True, 'students_count': 0, 'samples_count': 0, 'message': 'No student datasets found. Model cleared.'}

            total_folders = len(student_folders)
            processed_samples = 0
            
            for idx, student_id in enumerate(student_folders):
                # Lookup student in DB
                student = StudentModel.get_by_student_id(student_id)
                if not student or student.get('status') != 'active':
                    continue
                
                face_label = student['face_label']
                
                s_dir = os.path.join(dataset_dir, student_id)
                image_files = [f for f in os.listdir(s_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png')) and f != 'profile.jpg']
                
                student_face_count = 0
                for img_name in image_files:
                    img_path = os.path.join(s_dir, img_name)
                    try:
                        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                        if img is None:
                            continue
                        
                        # Ensure standard size and equalization
                        if img.shape != Config.FACE_IMAGE_SIZE:
                            img = cv2.resize(img, Config.FACE_IMAGE_SIZE)
                        
                        faces.append(img)
                        labels.append(int(face_label))
                        processed_samples += 1
                        student_face_count += 1
                    except Exception as img_err:
                        print(f"Skipping corrupted image {img_path}: {img_err}")
                
                if student_face_count > 0:
                    labels_map[str(face_label)] = {
                        'student_id': student['student_id'],
                        'name': student['name'],
                        'department': student['department'],
                        'semester': student['semester']
                    }
                
                with self.lock:
                    prog = int(10 + (idx / total_folders) * 60)
                    self.training_status = {'status': 'in_progress', 'progress': prog, 'message': f'Processing {student["name"]} ({idx+1}/{total_folders})...'}

            if len(faces) == 0 or len(labels_map) == 0:
                self.clear_model()
                return {'success': True, 'students_count': 0, 'samples_count': 0, 'message': 'No valid face samples. Model cleared.'}

            with self.lock:
                self.training_status = {'status': 'in_progress', 'progress': 80, 'message': 'Training LBPH Face Recognizer...'}

            # Train Recognizer
            self.recognizer.train(faces, np.array(labels, dtype=np.int32))
            
            # Save Model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.recognizer.write(self.model_path)
            
            # Save Label Mappings
            with open(self.labels_path, 'w', encoding='utf-8') as f:
                json.dump(labels_map, f, indent=2)

            self.labels_map = labels_map
            self.is_trained = True
            self.last_trained_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with self.lock:
                self.training_status = {
                    'status': 'completed',
                    'progress': 100,
                    'message': f'Trained successfully on {len(labels_map)} students ({processed_samples} samples)'
                }
            
            try:
                ActivityLogModel.log('TRAIN_MODEL', f'Model retrained with {len(labels_map)} students and {processed_samples} samples')
            except Exception:
                pass

            return {
                'success': True,
                'students_count': len(labels_map),
                'samples_count': processed_samples,
                'last_trained': self.last_trained_time
            }

        except Exception as e:
            with self.lock:
                self.training_status = {'status': 'failed', 'progress': 0, 'message': f'Training failed: {str(e)}'}
            return {'success': False, 'message': str(e)}

    def predict(self, face_gray_crop, min_confidence=70.0):
        """
        Predicts face identity from a grayscale 200x200 crop.
        Returns dict with match status, student info, confidence %, and distance.
        """
        if not self.is_trained or not self.recognizer or len(self.labels_map) == 0:
            return {'recognized': False, 'status': 'model_not_trained', 'confidence': 0.0, 'message': 'Model not trained'}

        if face_gray_crop is None or face_gray_crop.size == 0:
            return {'recognized': False, 'status': 'invalid_crop', 'confidence': 0.0, 'message': 'Empty face crop'}

        try:
            # Resize if needed
            if face_gray_crop.shape != Config.FACE_IMAGE_SIZE:
                face_gray_crop = cv2.resize(face_gray_crop, Config.FACE_IMAGE_SIZE)
            
            label, distance = self.recognizer.predict(face_gray_crop)
            
            # LBPH Distance formula conversion to intuitive Confidence %
            confidence = max(0.0, min(100.0, round(100.0 - (distance * 0.65), 1)))
            
            label_str = str(label)
            if label_str in self.labels_map and confidence >= min_confidence:
                student_info = self.labels_map[label_str]
                
                # Check that student is actively registered in database
                try:
                    st_db = StudentModel.get_by_student_id(student_info['student_id'])
                    if not st_db or st_db.get('status') != 'active' or st_db.get('face_samples_count', 0) == 0:
                        return {
                            'recognized': False,
                            'status': 'unknown',
                            'confidence': confidence,
                            'distance': round(distance, 1),
                            'message': 'Unregistered / Removed Face'
                        }
                except Exception:
                    pass

                return {
                    'recognized': True,
                    'status': 'recognized',
                    'student_id': student_info['student_id'],
                    'name': student_info['name'],
                    'department': student_info.get('department', ''),
                    'semester': student_info.get('semester', ''),
                    'confidence': confidence,
                    'distance': round(distance, 1),
                    'face_label': label
                }
            elif label_str in self.labels_map and confidence < min_confidence:
                return {
                    'recognized': False,
                    'status': 'low_confidence',
                    'confidence': confidence,
                    'distance': round(distance, 1),
                    'message': 'Confidence below required threshold'
                }
            else:
                return {
                    'recognized': False,
                    'status': 'unknown',
                    'confidence': confidence,
                    'distance': round(distance, 1),
                    'message': 'Unknown person'
                }

        except Exception as e:
            return {'recognized': False, 'status': 'error', 'confidence': 0.0, 'message': str(e)}


face_recognizer = FaceRecognitionService()
