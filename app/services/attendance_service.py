import cv2
import time
import threading
import numpy as np
from datetime import datetime, date
from app.config import Config
from app.services.face_detection import detector
from app.services.face_recognition import face_recognizer
from app.database.models import AttendanceModel, StudentModel, SettingsModel, ActivityLogModel


class AttendanceService:
    def __init__(self):
        self.cooldown_cache = {} # {student_id: timestamp_last_processed}
        self.marked_today_set = set() # {student_id} cached for today
        self.last_cache_date = None
        self.recent_recognitions = [] # Circular buffer of last 10 recognitions for live dashboard
        self.lock = threading.Lock()
        self.active_camera = None


    def get_confidence_threshold(self):
        try:
            val = SettingsModel.get('confidence_threshold', Config.CONFIDENCE_THRESHOLD)
            return float(val)
        except:
            return Config.CONFIDENCE_THRESHOLD

    def get_cooldown_seconds(self):
        try:
            val = SettingsModel.get('cooldown_minutes', Config.DUPLICATE_COOLDOWN_MINUTES)
            return int(val) * 60
        except:
            return Config.DUPLICATE_COOLDOWN_MINUTES * 60

    def process_live_frame(self, frame):
        """
        Processes frame for real-time live attendance:
        1. Detects all faces in frame
        2. Predicts student identity
        3. Checks duplicate rules & marks attendance in DB
        4. Overlays futuristic visual bounding boxes & HUD info
        Returns: (annotated_frame, list_of_detected_events)
        """
        if frame is None or frame.size == 0:
            return frame, []

        annotated = frame.copy()
        h, w = frame.shape[:2]
        faces = detector.detect_faces(frame)
        events = []
        min_conf = self.get_confidence_threshold()
        cooldown_sec = self.get_cooldown_seconds()
        now_ts = time.time()
        now_str = datetime.now().strftime('%H:%M:%S')

        for (x, y, fw, fh) in faces:
            face_crop = detector.extract_face(frame, (x, y, fw, fh), target_size=Config.FACE_IMAGE_SIZE)
            pred = face_recognizer.predict(face_crop, min_confidence=min_conf)
            
            event_data = {
                'timestamp': now_str,
                'bbox': [int(x), int(y), int(fw), int(fh)]
            }

            if pred['recognized']:
                student_id = pred['student_id']
                name = pred['name']
                confidence = pred['confidence']
                dept = pred.get('department', '')
                
                # Check in-memory today cache
                today_str = date.today().isoformat()
                if self.last_cache_date != today_str:
                    self.last_cache_date = today_str
                    self.marked_today_set.clear()

                is_already_marked = student_id in self.marked_today_set
                if not is_already_marked:
                    # Check DB for attendance status today
                    is_already_marked = AttendanceModel.is_marked_today(student_id)
                    if is_already_marked:
                        self.marked_today_set.add(student_id)
                
                # Check in-memory cooldown to avoid spamming the log every frame
                last_proc = self.cooldown_cache.get(student_id, 0)
                in_cooldown = (now_ts - last_proc) < cooldown_sec

                if not is_already_marked:
                    # Mark Attendance in DB
                    mark_res = AttendanceModel.mark_present(student_id, confidence, recognition_method='OpenCV-LBPH')
                    if mark_res and mark_res.get('status') == 'marked':
                        self.marked_today_set.add(student_id)
                        self.cooldown_cache[student_id] = now_ts
                        
                        event_data.update({
                            'status': 'Marked Present',
                            'type': 'success',
                            'student_id': student_id,
                            'name': name,
                            'confidence': confidence,
                            'department': dept,
                            'message': 'Attendance marked successfully'
                        })
                        try:
                            ActivityLogModel.log('ATTENDANCE_MARKED', f'Marked present for {name} ({student_id}) with {confidence}% confidence', student_id=student_id)
                        except Exception:
                            pass
                        
                        # Box Style: Glowing Emerald Green (BGR: 46, 204, 64)
                        box_color = (64, 204, 46)
                        badge_title = f"{name} ({confidence}%)"
                        status_sub = "ATTENDANCE RECORDED"
                    else:
                        self.cooldown_cache[student_id] = now_ts
                        event_data.update({
                            'status': 'Already Marked' if mark_res.get('status') == 'already_marked' else 'Recognized',
                            'type': 'info',
                            'student_id': student_id,
                            'name': name,
                            'confidence': confidence,
                            'department': dept,
                            'message': mark_res.get('message', 'Already recorded today')
                        })
                        box_color = (235, 189, 56)
                        badge_title = f"{name} ({confidence}%)"
                        status_sub = "ALREADY RECORDED TODAY"

                else:
                    # Already marked today
                    self.cooldown_cache[student_id] = now_ts
                    event_data.update({
                        'status': 'Already Marked',
                        'type': 'info',
                        'student_id': student_id,
                        'name': name,
                        'confidence': confidence,
                        'department': dept,
                        'message': 'Already recorded today'
                    })
                    # Box Style: Tech Cyan (BGR: 235, 189, 56)
                    box_color = (235, 189, 56)
                    badge_title = f"{name} ({confidence}%)"
                    status_sub = "ALREADY RECORDED TODAY"



                # Update live circular buffer
                with self.lock:
                    self._push_recent_recognition(event_data)

            elif pred['status'] == 'low_confidence':
                event_data.update({
                    'status': 'Low Confidence',
                    'type': 'warning',
                    'confidence': pred['confidence'],
                    'message': 'Face match uncertain'
                })
                # Box Style: Amber Warning (BGR: 11, 158, 245)
                box_color = (11, 158, 245)
                badge_title = f"Uncertain ({pred['confidence']}%)"
                status_sub = "LOW CONFIDENCE MATCH"

            else: # Unknown or not trained
                event_data.update({
                    'status': 'Unknown Person',
                    'type': 'danger',
                    'confidence': pred.get('confidence', 0.0),
                    'message': 'Unregistered Face'
                })
                # Box Style: Crimson Danger (BGR: 68, 68, 239)
                box_color = (68, 68, 239)
                badge_title = "Unknown Person"
                status_sub = "UNREGISTERED FACE"

            events.append(event_data)

            # Draw Modern Sci-Fi / SaaS Corner Bounding Box
            self._draw_modern_bbox(annotated, x, y, fw, fh, box_color, badge_title, status_sub)

        return annotated, events

    def _draw_modern_bbox(self, img, x, y, w, h, color, title, subtitle):
        """Draws polished high-tech corner brackets and label card."""
        line_len = int(min(w, h) * 0.25)
        thickness = 2
        corner_thick = 3
        
        # Main subtle rectangle
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 1, cv2.LINE_AA)
        
        # Corner brackets for premium CV console look
        # Top-Left
        cv2.line(img, (x, y), (x + line_len, y), color, corner_thick, cv2.LINE_AA)
        cv2.line(img, (x, y), (x, y + line_len), color, corner_thick, cv2.LINE_AA)
        # Top-Right
        cv2.line(img, (x + w, y), (x + w - line_len, y), color, corner_thick, cv2.LINE_AA)
        cv2.line(img, (x + w, y), (x + w, y + line_len), color, corner_thick, cv2.LINE_AA)
        # Bottom-Left
        cv2.line(img, (x, y + h), (x + line_len, y + h), color, corner_thick, cv2.LINE_AA)
        cv2.line(img, (x, y + h), (x, y + h - line_len), color, corner_thick, cv2.LINE_AA)
        # Bottom-Right
        cv2.line(img, (x + w, y + h), (x + w - line_len, y + h), color, corner_thick, cv2.LINE_AA)
        cv2.line(img, (x + w, y + h), (x + w, y + h - line_len), color, corner_thick, cv2.LINE_AA)

        # Draw Bottom Floating Card for Title & Subtitle
        card_h = 38
        card_y = y + h + 8 if (y + h + 8 + card_h) < img.shape[0] else max(0, y - card_h - 8)
        card_w = max(w, 180)
        
        # Dark translucent card background
        sub_img = img[card_y:card_y+card_h, x:x+card_w]
        if sub_img.shape[0] == card_h and sub_img.shape[1] == card_w:
            black_rect = np.zeros(sub_img.shape, dtype=np.uint8)
            res = cv2.addWeighted(sub_img, 0.2, black_rect, 0.8, 1.0)
            img[card_y:card_y+card_h, x:x+card_w] = res
            cv2.rectangle(img, (x, card_y), (x + card_w, card_y + card_h), color, 1, cv2.LINE_AA)
            cv2.putText(img, title, (x + 6, card_y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(img, subtitle, (x + 6, card_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1, cv2.LINE_AA)

    def _push_recent_recognition(self, item):
        # Keep last 15 recognitions
        self.recent_recognitions.insert(0, item)
        if len(self.recent_recognitions) > 15:
            self.recent_recognitions.pop()

    def get_recent_live_events(self):
        with self.lock:
            return list(self.recent_recognitions)

attendance_engine = AttendanceService()
