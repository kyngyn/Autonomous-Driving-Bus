import cv2
import socket

width, height = 480, 360
ip = 'HOST'

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (ip, 2000)
sock.connect(server_address)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    frame = cv2.resize(frame, (width, height))
    #frame = cv2.flip(frame, -1) # 영상 뒤집기

    try:
        frame, angle = detect_lane(frame)
        print(angle)
        sock.send(angle.encode())
    except:
        pass    

    cv2.imshow('detect', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
cap.release()
