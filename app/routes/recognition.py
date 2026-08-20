import cv2
import time
import threading
import numpy as np
from flask import Blueprint, render_template, Response, jsonify, request
from app.config import Config
from app.routes.auth import login_required
from app.services.attendance_service import attendance_engine
from app.services.face_capture import capture_manager
from app.services.face_recognition import face_recognizer
from app.database.models import StudentModel, SettingsModel

recognition_bp = Blueprint('recognition', __name__)

class CameraManager:
    def __init__(self):
        self.cap = None
        self.lock = threading.Lock()
        self.latest_frame = None
        self.is_running = False
        self.thread = None
        self.cached_index = None
        self.last_attempt = 0
        self.placeholder_frame = self._generate_no_camera_frame()

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _get_configured_index(self):
        try:
            return int(SettingsModel.get('camera_index', Config.CAMERA_INDEX))
        except:
            return Config.CAMERA_INDEX

    def _open_capture(self):
        cam_idx = self._get_configured_index() if self.cached_index is None else self.cached_index
        indices = [cam_idx] if cam_idx == 0 else [cam_idx, 0]
        
        for idx in indices:
            try:
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    cap = cv2.VideoCapture(idx)
                
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.cached_index = idx
                        return cap
                    cap.release()
            except Exception as e:
                pass
        return None

    def _capture_loop(self):
        while self.is_running:
            if self.cap is None or not self.cap.isOpened():
                now = time.time()
                if now - self.last_attempt >= 1.0:
                    self.last_attempt = now
                    self.cap = self._open_capture()
                if self.cap is None:
                    time.sleep(0.1)
                    continue

            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    with self.lock:
                        self.latest_frame = frame
                else:
                    if self.cap is not None:
                        self.cap.release()
                        self.cap = None
                    time.sleep(0.1)
            except Exception:
                if self.cap is not None:
                    self.cap.release()
                    self.cap = None
                time.sleep(0.1)
            time.sleep(0.015)

    def read_frame(self):
        if not self.is_running:
            self.start()

        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()

        return self.placeholder_frame

    def release(self):
        self.is_running = False
        with self.lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self.latest_frame = None

    def _generate_no_camera_frame(self):
        # Create a dark tech placeholder frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (20, 16, 11)
        for x in range(0, 640, 40):
            cv2.line(frame, (x, 0), (x, 480), (30, 24, 18), 1)
        for y in range(0, 480, 40):
            cv2.line(frame, (0, y), (640, y), (30, 24, 18), 1)
            
        cv2.putText(frame, "LIVE CAMERA STREAM INITIALIZING...", (100, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "DirectShow hardware link active", (190, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (160, 160, 160), 1, cv2.LINE_AA)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"System Clock: {ts}", (210, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 200, 100), 1, cv2.LINE_AA)
        return frame

camera_manager = CameraManager()
camera_manager.start()


@recognition_bp.route('/live')
@login_required
def live_page():
    return render_template(
        'recognition/live.html',
        is_trained=face_recognizer.is_trained,
        last_trained=face_recognizer.last_trained_time,
        registered_count=len(face_recognizer.labels_map)
    )

def generate_live_stream(app):
    """MJPEG streaming generator for live attendance."""
    with app.app_context():
        while True:
            try:
                frame = camera_manager.read_frame()
                annotated_frame, events = attendance_engine.process_live_frame(frame)
                
                # Fast JPEG encode at 70% quality (crisp image + lightweight payload)
                ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if not ret:
                    time.sleep(0.01)
                    continue
                    
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                print(f"Live stream error: {e}")
                time.sleep(0.05)
            time.sleep(0.015) # Real-time silky smooth streaming

@recognition_bp.route('/video_feed')
@login_required
def video_feed():
    from flask import current_app
    app = current_app._get_current_object()
    return Response(generate_live_stream(app), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_capture_stream(app, student_id):
    """MJPEG streaming generator for face dataset capture."""
    with app.app_context():
        while True:
            try:
                frame = camera_manager.read_frame()
                annotated, session = capture_manager.process_capture_frame(student_id, frame)
                
                ret, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if not ret:
                    time.sleep(0.01)
                    continue
                    
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                       
                if session and session.get('status') == 'completed':
                    time.sleep(0.3)
                    break
            except Exception as e:
                print(f"Capture stream error: {e}")
                time.sleep(0.05)
            time.sleep(0.015)

@recognition_bp.route('/capture_feed/<student_id>')
@login_required
def capture_feed(student_id):
    from flask import current_app

    app = current_app._get_current_object()
    return Response(generate_capture_stream(app, student_id), mimetype='multipart/x-mixed-replace; boundary=frame')


@recognition_bp.route('/api/capture_status/<student_id>')
@login_required
def capture_status(student_id):
    info = capture_manager.get_dataset_info(student_id)
    return jsonify(info)

@recognition_bp.route('/api/capture_manual_sample/<student_id>', methods=['POST'])
@login_required
def capture_manual_sample(student_id):
    slot = request.json.get('slot') if request.is_json else request.form.get('slot')
    frame = camera_manager.read_frame()
    result = capture_manager.capture_single_sample(student_id, frame, target_slot=slot)
    return jsonify(result)

@recognition_bp.route('/api/delete_sample_image/<student_id>/<filename>', methods=['POST'])
@login_required
def delete_sample_image(student_id, filename):
    result = capture_manager.delete_single_sample(student_id, filename)
    return jsonify(result)

@recognition_bp.route('/api/reset_capture/<student_id>', methods=['POST'])
@login_required
def reset_capture(student_id):
    result = capture_manager.reset_dataset(student_id)
    try:
        face_recognizer.train_model()
    except Exception as e:
        print(f"Error syncing model on reset: {e}")
    return jsonify(result)



@recognition_bp.route('/api/train', methods=['POST'])
@login_required
def train_model():
    result = face_recognizer.train_model()
    return jsonify(result)

@recognition_bp.route('/api/training_status')
@login_required
def training_status():
    with face_recognizer.lock:
        status_copy = dict(face_recognizer.training_status)
    status_copy['is_trained'] = face_recognizer.is_trained
    status_copy['last_trained'] = face_recognizer.last_trained_time
    status_copy['registered_count'] = len(face_recognizer.labels_map)
    return jsonify(status_copy)

@recognition_bp.route('/api/live_status')
@login_required
def live_status():
    events = attendance_engine.get_recent_live_events()
    return jsonify({
        'recent_events': events,
        'model_trained': face_recognizer.is_trained,
        'registered_count': len(face_recognizer.labels_map)
    })
