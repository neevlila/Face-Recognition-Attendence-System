import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    print("=" * 60)
    print("  AuraPass AI - Intelligent Real-Time Face Attendance System")
    print(f"  Running on: http://{host}:{port}")
    print("  Default Admin: admin / admin123")
    print("=" * 60)

    
    app.run(host=host, port=port, debug=debug, threaded=True)
