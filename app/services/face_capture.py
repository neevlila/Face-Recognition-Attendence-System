import os
import cv2
import time
import threading
import numpy as np
from app.config import Config
from app.services.face_detection import detector
from app.database.models import StudentModel

POSE_PROMPTS = [
    "Pose 1: Look directly straight at the camera (Neutral expression)",
    "Pose 2: Turn head slightly to the RIGHT (~15°)",
    "Pose 3: Turn head slightly to the LEFT (~15°)",
    "Pose 4: Look straight with a natural SMILE",
    "Pose 5: Tilt head slightly UPWARDS (~10°)",
    "Pose 6: Tilt head slightly DOWNWARDS (~10°)"
]

class FaceCaptureManager:
    def __init__(self):
        self.lock = threading.Lock()

    def get_dataset_info(self, student_id):
        """Returns list of existing sample files and current count for student."""
        with self.lock:
            student_dir = os.path.join(Config.DATASET_DIR, str(student_id))
            os.makedirs(student_dir, exist_ok=True)
            files = [f for f in os.listdir(student_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png')) and f != 'profile.jpg']
            files.sort()
            return {
                'student_id': str(student_id),
                'student_dir': student_dir,
                'samples': files,
                'count': len(files),
                'target': Config.SAMPLES_PER_STUDENT,
                'has_profile': os.path.exists(os.path.join(student_dir, 'profile.jpg'))
            }

    def capture_single_sample(self, student_id, frame, target_slot=None):
        """
        Manually captures one face snapshot from the provided frame.
        target_slot: optional 1-indexed slot number (1 to 6) for retake.
        """
        with self.lock:
            student_id_str = str(student_id)
            student_dir = os.path.join(Config.DATASET_DIR, student_id_str)
            os.makedirs(student_dir, exist_ok=True)

            if frame is None or frame.size == 0:
                return {'success': False, 'message': 'Camera frame is empty or offline'}

            # Detect faces in frame
            faces = detector.detect_faces(frame)
            if len(faces) == 0:
                return {'success': False, 'message': 'No face detected in camera view. Look directly at the camera.'}
            if len(faces) > 1:
                return {'success': False, 'message': 'Multiple faces detected! Ensure only the student is in frame.'}

            fx, fy, fw, fh = faces[0]
            face_crop = detector.extract_face(frame, (fx, fy, fw, fh), target_size=Config.FACE_IMAGE_SIZE)
            is_good, q_info, q_msg = detector.assess_quality(face_crop)

            # Determine filename
            existing = [f for f in os.listdir(student_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png')) and f != 'profile.jpg']
            existing.sort()

            if target_slot is not None and 1 <= int(target_slot) <= 6:
                slot_num = int(target_slot)
            else:
                slot_num = len(existing) + 1

            filename = f"{slot_num:03d}.jpg"
            filepath = os.path.join(student_dir, filename)
            cv2.imwrite(filepath, face_crop)

            # Update/save profile thumbnail if slot is 1 or profile.jpg doesn't exist
            profile_path = os.path.join(student_dir, "profile.jpg")
            if slot_num == 1 or not os.path.exists(profile_path):
                h, w = frame.shape[:2]
                crop_color = frame[max(0, fy-20):min(h, fy+fh+20), max(0, fx-20):min(w, fx+fw+20)]
                if crop_color.size > 0:
                    cv2.imwrite(profile_path, crop_color)

            # Update sample count in DB
            all_samples = [f for f in os.listdir(student_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png')) and f != 'profile.jpg']
            total_count = len(all_samples)
            StudentModel.update_samples_count(student_id_str, total_count)

            return {
                'success': True,
                'message': f'Image #{slot_num} captured successfully!',
                'slot': slot_num,
                'count': total_count,
                'target': Config.SAMPLES_PER_STUDENT,
                'filename': filename,
                'quality': q_info
            }

    def delete_single_sample(self, student_id, filename):
        """Deletes a specific sample image from dataset."""
        with self.lock:
            student_id_str = str(student_id)
            student_dir = os.path.join(Config.DATASET_DIR, student_id_str)
            filepath = os.path.join(student_dir, filename)

            if os.path.exists(filepath) and filename != 'profile.jpg':
                try:
                    os.remove(filepath)
                except Exception as e:
                    return {'success': False, 'message': str(e)}

            all_samples = [f for f in os.listdir(student_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png')) and f != 'profile.jpg']
            total_count = len(all_samples)
            StudentModel.update_samples_count(student_id_str, total_count)

            return {
                'success': True,
                'message': f'Sample {filename} deleted',
                'count': total_count,
                'target': Config.SAMPLES_PER_STUDENT
            }

    def reset_dataset(self, student_id):
        """Clears all sample images for the student."""
        with self.lock:
            student_id_str = str(student_id)
            student_dir = os.path.join(Config.DATASET_DIR, student_id_str)
            if os.path.exists(student_dir):
                for f in os.listdir(student_dir):
                    if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                        try:
                            os.remove(os.path.join(student_dir, f))
                        except:
                            pass
            StudentModel.update_samples_count(student_id_str, 0)
            return {'success': True, 'count': 0}

    def process_capture_frame(self, student_id, frame):
        """
        Live preview with visual framing guide and pose helper.
        Does NOT automatically capture — allows user to frame and hit 'Capture'.
        """
        if frame is None or frame.size == 0:
            return frame, {'status': 'offline', 'message': 'Camera offline'}

        annotated = frame.copy()
        h, w = frame.shape[:2]

        faces = detector.detect_faces(frame)
        info = self.get_dataset_info(student_id)
        current_count = info['count']
        target_count = info['target']

        # Guide overlay box
        guide_w, guide_h = int(w * 0.45), int(h * 0.55)
        gx1 = (w - guide_w) // 2
        gy1 = (h - guide_h) // 2
        gx2 = gx1 + guide_w
        gy2 = gy1 + guide_h

        # Overlay center guide box
        cv2.rectangle(annotated, (gx1, gy1), (gx2, gy2), (80, 80, 100), 1, cv2.LINE_AA)

        next_slot = min(current_count + 1, target_count)
        pose_prompt = POSE_PROMPTS[next_slot - 1] if next_slot <= len(POSE_PROMPTS) else "All 6 poses captured!"

        if len(faces) == 0:
            box_color = (0, 0, 255)
            status_msg = "No face detected - look directly at camera"
        elif len(faces) > 1:
            box_color = (0, 165, 255)
            status_msg = "Multiple faces detected - only 1 person allowed"
            for (fx, fy, fw, fh) in faces:
                cv2.rectangle(annotated, (fx, fy), (fx + fw, fy + fh), box_color, 2)
        else:
            fx, fy, fw, fh = faces[0]
            face_crop = detector.extract_face(frame, (fx, fy, fw, fh), target_size=Config.FACE_IMAGE_SIZE)
            is_good, q_info, q_msg = detector.assess_quality(face_crop)
            box_color = (0, 255, 0) if is_good else (0, 200, 255)
            status_msg = "Face in position - Click 'Capture Shot'" if is_good else q_msg
            cv2.rectangle(annotated, (fx, fy), (fx + fw, fy + fh), box_color, 2)

        # Draw HUD overlays on preview
        cv2.putText(annotated, f"Dataset: {current_count}/{target_count} Images Captured", (25, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(annotated, pose_prompt, (25, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (56, 189, 248), 1, cv2.LINE_AA)
        cv2.putText(annotated, status_msg, (25, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.52, box_color, 1, cv2.LINE_AA)

        return annotated, {
            'student_id': str(student_id),
            'count': current_count,
            'target': target_count,
            'ready': len(faces) == 1,
            'message': status_msg,
            'pose': pose_prompt
        }

capture_manager = FaceCaptureManager()
