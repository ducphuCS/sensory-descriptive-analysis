import os
import subprocess
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Service Configuration
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "127.0.0.1")
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "8501")

def main():
    print(f"Starting FastAPI Backend (port {BACKEND_PORT})...")
    backend_process = subprocess.Popen(
        ["uv", "run", "uvicorn", "backend.app:app", "--host", BACKEND_HOST, "--port", BACKEND_PORT]
    )
    
    # Wait a short moment for backend to initialize
    time.sleep(2)
    
    print(f"Starting Streamlit Frontend (port {FRONTEND_PORT})...")
    frontend_process = subprocess.Popen(
        [
            "uv", "run", "streamlit", "run", "frontend/app.py", 
            "--server.port", FRONTEND_PORT, 
            "--server.address", FRONTEND_HOST
        ]
    )
    
    try:
        # Keep the launcher script active
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down dashboard processes...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("Dashboard shutdown complete.")

if __name__ == '__main__':
    main()
