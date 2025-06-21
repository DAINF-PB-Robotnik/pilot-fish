import logging
import cv2
import RPi.GPIO as GPIO
import time

from picamera2 import Picamera2

from config    import setup_logging, CAMERA_FORMAT, CAMERA_RESOLUTION, CAMERA_FRAMERATE
from track     import Track
from draw      import Draw
from control   import Control
from direction import Direction

class Main:
    def __init__(self):
        setup_logging()
        logging.info("Initialization successful.")

        self.tracker    = Track()
        self.control = Control()
        self.drawer     = Draw()

        # Configure & start camera entirely from config
        self.camera = Picamera2()
        self.camera.configure(
            self.camera.create_preview_configuration(
                main     = {"format": CAMERA_FORMAT, "size": CAMERA_RESOLUTION},
                controls = {"FrameRate": CAMERA_FRAMERATE}
            )
        )
        self.camera.start()
        logging.info("Camera started")
        '''
             #comeca
    
    picamv2= Picamera2()
    picamv2.configure(picamv2.create_video_configuration())
    picamv2.start()
    time.sleep(2)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi',fourcc,20,(640,480))
    start = time.time()
           
    print("gravando")
    while time.time() - start < 180:
        frame = picamv2.capture_array()
        frame = cv2.resize(frame, (640,480))
        out.write(frame)
                 
    out.release()
    picamv2.stop()
    print("Video salvo")
             
            #termina
'''
    def run(self):
        while True:
            frame = self.camera.capture_array()
            
            # 1) FPS tracking moved into Track
            inst_fps, _ = self.tracker.track_fps()

            # 2) Detection + movement
            contour, mask = self.tracker.track_frame(frame)
            self.control.move(frame, contour)

            # 3) Draw overlays (instantaneous FPS only)
            out, bin_mask = self.drawer.render(frame, contour, mask, inst_fps)

            # 4) Display
            #cv2.imshow("BINARY", bin_mask)
            cv2.imshow("MAIN",   out)
            if cv2.waitKey(1) != -1:
                break
                
       
        self.camera.stop()
        cv2.destroyAllWindows()
        GPIO.cleanup()
        

if __name__ == "__main__":
    Main().run()
