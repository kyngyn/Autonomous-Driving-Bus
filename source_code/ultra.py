from __future__ import division
import RPi.GPIO as GPIO
import socket,time
import pygame

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (ip, 1002)
sock.connect(server_address)
print("sensor connected...")

pygame.mixer.init(17000)
pygame.mixer.music.load('stop.mp3')
pygame.mixer.music.set_volume(1)

GPIO.setmode(GPIO.BOARD)

try :
    trig = 18
    echo = 16
    GPIO.setup(trig, GPIO.OUT)
    GPIO.setup(echo, GPIO.IN)
    print("초음파 센서")
    while True:
        GPIO.output(trig, False)
        time.sleep(0.5)
        GPIO.output(trig, True)
        time.sleep(0.00001)
        GPIO.output(trig, False)

        while GPIO.input(echo) == 0:
            pulse_s = time.time()
        while GPIO.input(echo) == 1:
            pulse_e = time.time()

        duration = pulse_e - pulse_s
        distance = duration * 17000
        distance = round(distance, 2)
        if (distance < 15):
            sock.send("stop".encode())
            print("장애물이 감지되었습니다!")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                continue
        else:
            sock.send("departure".encode())

except :
        GPIO.cleanup()
