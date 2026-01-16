
import sys
import os
from pathlib import Path

print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")

try:
    print("Attempting to import cv2...")
    import cv2
    print(f"cv2 imported successfully. Version: {cv2.__version__}")
except ImportError as e:
    print(f"ERROR: Failed to import cv2: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Unexpected error importing cv2: {e}")
    sys.exit(1)

try:
    print("Attempting to import httpx...")
    import httpx
    print(f"httpx imported successfully. Version: {httpx.__version__}")
except ImportError as e:
    print(f"ERROR: Failed to import httpx: {e}")
    sys.exit(1)

mp4_dir = Path("mp4")
if not mp4_dir.exists():
    print("ERROR: mp4 directory does not exist.")
    sys.exit(1)

mp4_files = list(mp4_dir.glob("*.mp4"))
print(f"Found {len(mp4_files)} mp4 files.")

if not mp4_files:
    print("No mp4 files to test.")
    sys.exit(0)

test_file = mp4_files[0]
print(f"Testing video read on: {test_file}")

try:
    cap = cv2.VideoCapture(str(test_file))
    if not cap.isOpened():
        print("ERROR: Could not open video file.")
    else:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Video opened. Total frames: {frame_count}")
        ret, frame = cap.read()
        if ret:
            print("Successfully read a frame.")
        else:
            print("ERROR: Failed to read frame.")
    cap.release()
except Exception as e:
    print(f"ERROR during video processing: {e}")
