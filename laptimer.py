from datetime import datetime
import time
import picamera
import sys
import RPi.GPIO as GPIO

# インターバル ５秒
INTERVAL = 5

PATH = "/mnt/usb1/movie/"

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN)
GPIO.setup(23, GPIO.OUT) 

if __name__ == '__main__':
    try:
        with picamera.PiCamera() as camera:
            #reverse
            camera.hflip = True
            camera.vflip = True
            #解像度の調整
            camera.resolution = (1280, 720)
            # 明るさの調整
            camera.brightness = 50
            print ("処理キャンセルはCTRL+C")
            while(True):
                # GPIO_PIN18と同値(センサーが動作を感知)
                if(GPIO.input(18) == GPIO.HIGH):
                    start_time = time.time()
                    # filename
                    now = time.ctime()
                    cnvtime = time.strptime(now)
                    filename = PATH + time.strftime("%Y_%m_%d_%H_%M_%S", cnvtime) + ".h264"
                    #record start
                    camera.start_recording(filename)
                    # monitor preview
                    camera.start_preview()  
                    while(True):
                        GPIO.output(23, 1)
                        time.sleep(1)
                        if(GPIO.input(18) == GPIO.HIGH):
                            GPIO.output(23, 0)
                            end_time = time.time()
                            # レコーディング終了
                            camera.stop_recording()
                            lap_time = end_time-start_time
                            print(f"経過時間：{lap_time}")
                            break

    except KeyboardInterrupt:
        print("全処理終了")
    finally:
        GPIO.cleanup()
