import cv2
import socket
import pickle
import struct

def do_stream(client_socket,client_address):
    cap = cv2.VideoCapture('space_sample.mp4')
    cap.set(cv2.CAP_PROP_FPS,60)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            frame_data = pickle.dumps(frame)
            client_socket.sendall(struct.pack("Q", len(frame_data)))
            client_socket.sendall(frame_data)
            if cv2.waitKey(1) == 13:
                break
        cap.release()
        cv2.destroyAllWindows()
        return 200
    except:
        cap.release()
        cv2.destroyAllWindows()
        return None

def do_connect():
    server_socket.listen(5)
    print("Server is listening...")
    client_socket, client_address = server_socket.accept()
    print(f"Connection from {client_address} accepted")
    return client_socket, client_address

while True:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 8888))

    client_socket,client_address=do_connect()

    ret=200
    while ret is not None:
        ret=do_stream(client_socket,client_address)
