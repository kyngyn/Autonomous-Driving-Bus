from __future__ import division
import RPi.GPIO as GPIO
import socket
import time
import pygame
import MFRC522
from multiprocessing import Process, Queue

pygame.mixer.init(17000)
pygame.mixer.music.load('arrive.mp3')
pygame.mixer.music.set_volume(1)

ip = ''
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (ip, 1001)
sock.connect(server_address)
print("sensor connected...")

MIFAREReader = MFRC522.MFRC522()
print("RFID")
while True:
    (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
    if status == MIFAREReader.MI_OK:
        print("도착했습니다")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue
        sock.send("stop".encode())
        time.sleep(3)
    else :
        sock.send("departure".encode())
GPIO.cleanup()



