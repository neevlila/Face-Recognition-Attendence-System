import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'faceattend-secure-key-2026-supersecret-college-prod')
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # Paths
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'attendance.db'))

    DATASET_DIR = str(BASE_DIR / 'dataset')
    MODELS_DIR = str(BASE_DIR / 'models')
    EXPORTS_DIR = str(BASE_DIR / 'exports')
    
    # Model files
    TRAINER_MODEL_PATH = str(BASE_DIR / 'models' / 'trainer.yml')
    LABELS_MAP_PATH = str(BASE_DIR / 'models' / 'labels.json')
    
    # Face Recognition & Capture Parameters
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 70.0))
    DUPLICATE_COOLDOWN_MINUTES = int(os.getenv('COOLDOWN_MINUTES', 60))
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))
    SAMPLES_PER_STUDENT = int(os.getenv('SAMPLES_PER_STUDENT', 6))

    
    # Face Image Quality Parameters
    FACE_IMAGE_SIZE = (200, 200)
    MIN_FACE_SIZE = (80, 80)
    BLUR_THRESHOLD = 50.0  # Laplacian variance threshold
    
    @classmethod
    def init_app(cls):
        os.makedirs(cls.DATASET_DIR, exist_ok=True)
        os.makedirs(cls.MODELS_DIR, exist_ok=True)
        os.makedirs(cls.EXPORTS_DIR, exist_ok=True)
