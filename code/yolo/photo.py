# photo.py

import os
import time
import cv2

from picamera2 import Picamera2
from config    import CAMERA_FORMAT, CAMERA_RESOLUTION

def main():
    # 1) choose dataset type
    choices = {"1": "normal", "2": "light", "3": "shake"}
    while True:
        sel = input("Select mode (1: normal, 2: light, 3: shake): ").strip()
        if sel in choices:
            label = choices[sel]
            break
        print("Invalid choice, try again.")

    # 2) number of photos & interval
    count    = int(input("How many photos to take? ").strip())
    interval = float(input("Interval between photos (seconds)? ").strip())

    # 3) prepare output folder
    base_dir = os.path.dirname(__file__)
    out_dir  = os.path.join(base_dir, label)
    os.makedirs(out_dir, exist_ok=True)

    # 4) if folder already has photos, offer to delete them
    existing = [f for f in os.listdir(out_dir)
                if os.path.isfile(os.path.join(out_dir, f))]
    if existing:
        print(f"Folder '{label}' already contains {len(existing)} files.")
        resp = input("Delete existing photos? [y/N]: ").strip().lower()
        if resp == "y":
            for filename in existing:
                os.remove(os.path.join(out_dir, filename))
            print(f"Deleted {len(existing)} existing files.")
        else:
            print("Keeping existing photos; new images will be added alongside.")

    # 5) configure and start camera
    picam2 = Picamera2()
    cfg = picam2.create_preview_configuration(
        main={"format": CAMERA_FORMAT, "size": CAMERA_RESOLUTION}
    )
    picam2.configure(cfg)
    picam2.start()
    print(f"Starting capture: {count} shots into '{out_dir}' every {interval}s...")

    try:
        for i in range(1, count + 1):
            time.sleep(interval)
            frame = picam2.capture_array()
            filename = f"{label}_{i:04d}.jpg"
            path = os.path.join(out_dir, filename)

            # save as high-quality JPEG
            cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            print(f"  ✓ Saved {filename}")

    finally:
        picam2.stop()
        print("Capture complete, camera stopped.")

if __name__ == "__main__":
    main()
