# -*- coding: utf-8 -*-
import cv2
import numpy as np
import socket
from time import sleep

# 영상 회전 함수
def rotate(frame, angle):
    matrix = cv2.getRotationMatrix2D((width/2, height/2), angle, 1) # 회전 중심
    dst = cv2.warpAffine(frame, matrix, (width, height))
    return dst

# ROI
def ROI(frame, vertices, color3 = (255, 255, 255), color1 = 255):
    mask = np.zeros_like(frame) # img 크기와 같은 이미지(배열)
    
    if len(frame.shape) > 2: # 컬러 이미지(3채널)일 때
        color = color3
    else: # 흑백 이미지(1채널)일 때
        color = color1
        
    # mask에 vertices 점들로 이뤄진 다각형 부분을 color로 채움
    cv2.fillPoly(mask, vertices, color)
    
    # 이미지와 ROI를 합성
    ROI_img = cv2.bitwise_and(frame, mask)
    return ROI_img

# 선 그리기 함수
def draw_line(frame, lines, color = [0, 0, 255], thickness = 10): 
    cv2.line(frame, (lines[0], lines[1]), (lines[2], lines[3]), color, thickness)

# 대표선 추출 함수 
def get_fitline(frame, f_lines):   
    lines = np.squeeze(f_lines)
    lines = lines.reshape(lines.shape[0] * 2, 2) # 좌표값으로 변환
    vx, vy, x, y = cv2.fitLine(lines, cv2.DIST_L2, 0, 0.01, 0.01)
    
    x1, y1 = int((frame.shape[0] - y) / vy * vx + x) , int(frame.shape[0] - 20)
    x2, y2 = int(((frame.shape[0] / 2 + 100) - y) / vy * vx + x) , int(frame.shape[0] / 2 + 100 - 20)
      
    result = [x1, y1, x2, y2]
    #cv2.circle(img, (x1, y1), 5, (0, 0, 255), -1) # -1이면 내부 채워짐
    return result, x, y

def intersaction(L_line, R_line):
    m1 = (L_line[3] - L_line[1]) / (L_line[2] - L_line[0])
    m2 = (R_line[3] - R_line[1]) / (R_line[2] - R_line[0])

    #line1 = m1(x - L_line[0]) + L_line[1]
    #line2 = m2(x - R_line[0]) + R_line[1]

    x = int((R_line[1] - L_line[1] + L_line[0] * m1 - R_line[0] * m2) / (m1 - m2))
    y = int(m1 * (x - L_line[0]) + L_line[1])
    return (x, y)

    
def detect_lane(img):
    gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) # 흑백 이미지로 변환
    #cv2.imshow("gray", gray_img)

    blur_img = cv2.GaussianBlur(gray_img, (3, 3), 0) # Blur 효과
    #cv2.imshow("blur", blur_img)
    
    kernel = np.ones((5,5), np.uint8)
    dilation_img = cv2.dilate(blur_img, kernel, 1) # 팽창 연산
    #cv2.imshow("dilation", dilation_img)
    
    canny_img = cv2.Canny(dilation_img, 200, 300) # 외곽선 검출
    #cv2.imshow("canny", canny_img)

    vertices = np.array([[(0, height * 3 / 2)), (0, height - 30), (width, height - 30), (width, height * 3 / 2)]], dtype = np.int32)
    ROI_img = ROI(canny_img, vertices) # ROI 설정    
    img = cv2.polylines(img, vertices, True, (255, 0 ,0), 5)
    
    line_arr = cv2.HoughLinesP(ROI_img, 1, np.pi / 180, 10, 12, 10) # 직선 검출
    line_arr = np.squeeze(line_arr) # 불필요한 값 정리

    '''  
    print(line_arr)                 
    for i in range(0, len(line_arr)):
        l = line_arr[i, :]
        cv2.line(img, (l[0], l[1]), (l[2], l[3]), (0, 0, 255), 4)
        cv2.circle(img, (l[0], l[1]), 5, (0, 255, 0), -1)
    cv2.imshow("hough", img)
    '''  
    
    slope_degree = np.arctan2(line_arr[:, 1] - line_arr[:, 3], line_arr[:, 0] - line_arr[:, 2]) * 180 / np.pi # 기울기 구하기 arctan(y/x)
    
    # 수평 기울기 제한
    line_arr = line_arr[np.abs(slope_degree) < 170]
    slope_degree = slope_degree[np.abs(slope_degree) < 170]
    
    # 수직 기울기 제한
    line_arr = line_arr[np.abs(slope_degree) > 120]
    slope_degree = slope_degree[np.abs(slope_degree) > 120]

    L_lines, R_lines = line_arr[(slope_degree > 0), :], line_arr[(slope_degree < 0), :]
    
    if len(L_lines) == 0 or len(R_lines) == 0 : # 양쪽 차선 기울기 같거나 한쪽 차선만 인식될 때
        lines = line_arr[:, None]
        fit_line, x, y = get_fitline(img, lines)
        draw_line(img, fit_line)
        angle = np.arctan(fit_line)
        angle = mean(angle)
    else : 
        L_lines, R_lines = L_lines[:, None], R_lines[:, None]
       
        # 대표선 구하기
        left_fit_line, lx, ly = get_fitline(img, L_lines)
        right_fit_line, rx, ry = get_fitline(img, R_lines)

        # 대표선 그리기
        draw_line(img, left_fit_line)
        draw_line(img, right_fit_line)
        
        inter_point = intersaction(left_fit_line, right_fit_line) # 소실점
        center_point = int(lx + (rx - lx) / 2), int(max(ly, ry)) # 양쪽 차선 중심점 
        #cv2.circle(img, inter_point, 5, (0, 0, 255), -1) # -1이면 내부 채워짐
        #cv2.circle(img, center_point, 5, (0, 0, 255), -1)
        cv2.line(img, inter_point, center_point, (0, 255, 0), 5)        

        angle = np.arctan2(center_point[1] - inter_point[1], center_point[0] - inter_point[0]) * 180 / np.pi # 기울기 측정

    if inter_point[0] < center_point[0]:
        angle = int(angle) - 90
    else :
        angle = - (int(angle) - 90)
    
    return img, angle    

HOST=''
PORT=2000 

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((HOST,PORT))
s.listen(1)
print('Socket now listening..')
 
#연결, conn에는 소켓 객체, addr은 소켓에 바인드 된 주소
conn,addr=s.accept()
 
while True:
    # client에서 받은 stringData의 크기 (==(str(len(stringData))).encode().ljust(16))
    length = recvall(conn, 16)
    stringData = recvall(conn, int(length))
    data = np.fromstring(stringData, dtype = 'uint8')
    
    #data를 디코딩한다.
    frame = cv2.imdecode(data, 1)
    cv2.imshow('frame',frame)
    
    try:
        angle = detect_lane(frame)
        print(angle)
        cv2.imshow('result',frame)
        s.send(angle.encode())
    except:
        print("error")
        pass

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
    cv2.waitKey(1)
