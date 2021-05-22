# -*- coding: utf-8 -*-
from __future__ import division
import Adafruit_PCA9685
import RPi.GPIO as GPIO
import socket
import threading
from time import sleep
import pygame

ip1 = ' ' # 차선
ip2 = ' ' # RFID, 초음파

# 모터 상태
STOP  = 0
FORWARD  = 1
BACKWARD = 2

# PIN 입출력 설정
OUTPUT = 1
INPUT = 0

ENA = 26  # 37 pin
IN1 = 19  # 35 pin
IN2 = 13  # 33 pin

# GPIO 모드 설정 
GPIO.setmode(GPIO.BCM)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

DC = GPIO.PWM(ENA, 100)
DC.start(0)

pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(60) # 주파수 변경


# DC모터 제어 함수
def setMotorContor(DC, IN1, IN2, speed, state):
    DC.ChangeDutyCycle(speed) # PWM으로 제어 
    
    if state == FORWARD: # 전진
        GPIO.output(IN1, GPIO.HIGH)
        GPIO.output(IN2, GPIO.LOW)
        
    elif state == BACKWARD: # 후진
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.HIGH)
        
    elif state == STOP: # 정지
        GPIO.output(IN1, GPIO.LOW)
        GPIO.output(IN2, GPIO.LOW)
        
def setMotor(speed, state):
    setMotorContor(DC, IN1, IN2, speed, state)

angle = [241, 287, 322, 355, 400, 423, 446, 492] 
CENTER = 394

Bus_stop = False
Obstacle = False

def from_line():    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip1, 1000)
    print("line socket listening...")
    sock.bind(server_address)
    sock.listen(1)

    try:
        client, address = sock.accept()
        print("Line Connected")
        while True:
            data = client.recv(4)
            try:
                angle = int(data)
            except:
                continue
            if Bus_stop or Obstacle : # 버스 정류장, 장애물 인식시 정지
                setMotor(50, STOP)
            else:
                if abs(angle) < 10 : # 직진
                    pwm.set_pwm(0, 0, CENTER)         
                elif angle < -30 :
                pwm.set_pwm(0, 0, angle[0])
                elif -30 < angle < -20 :
                pwm.set_pwm(0, 0, angle[1])
                elif -20 < angle < -10 :
                    pwm.set_pwm(0, 0, angle[2])
                elif 10 < angle < 20 :
                    pwm.set_pwm(0, 0, angle[3]) 
                elif 20 < angle < 30 :
                    pwm.set_pwm(0, 0, angle[4])
                elif 30 < angle :
                    pwm.set_pwm(0, 0, angle[5])
                setMotor(50, FORWARD)        
    except:
        print("close line")
        GPIO.cleanup()
        exit(0)


def from_RFID():
    global Bus_stop, Obstacle
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip2, 1001)
    print("Sensor socket listening...")
    sock.bind(server_address)
    sock.listen(1)

    try:
        client, address = sock.accept()
        while True:
            data = client.recv(4)
            print(data)
            if data == "departure" and not Obstacle:
                setMotor(50, FORWARD)
                Bus_stop = False
            elif data == "arive":
                setMotor(50, STOP)
                sleep(5)
                Bus_stop = True
    except:
        print("close RFID")
        sock.close()
        GPIO.cleanup()
        exit(1)

def from_Ultra():
    global Obstacle, Bus_stop
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip2, 1002)
    print("ultrar socket listening...")
    sock.bind(server_address)
    sock.listen(1)

    try:
        client, address = sock.accept()
        while True:            
            data = client.recv(4)
            print(data)
            if data == "departure" and not Bus_stop:
                setMotor(50, FORWARD)
                Obstacle = False
            elif data == "stop":
                setMotor(50, STOP)
                sleep(5)
                Obstacle = True
    except:
        print("close ultra")
        sock.close()
        GPIO.cleanup()
        exit(1)

LINE = threading.Thread(target=from_line)
RFID = threading.Thread(target=from_RFID)
ULTRA = threading.Thread(target=from_Ultra)

LINE.start()
RFID.start()
ULTRA.start()

LINE.join()
RFID.join()
ULTRA.join()

pwm.set_pwm(0, 0, 0)
GPIO.cleanup()

