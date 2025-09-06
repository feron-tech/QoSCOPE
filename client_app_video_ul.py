import cv2
import socket
import pickle
import struct
import os
import time

def do_stream(client_socket, fps, width, height):
    cap = cv2.VideoCapture('space_sample.mp4')
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    try:
        while True:  # loop forever over the video
            if not cap.isOpened():
                print("[App Video] Failed to open video file, retrying...")
                cap = cv2.VideoCapture('space_sample.mp4')
                cap.set(cv2.CAP_PROP_FPS, fps)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            ret, frame = cap.read()
            if not ret:
                print("[App Video] Video ended, restarting...")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # rewind video to start
                continue

            frame_data = pickle.dumps(frame)
            client_socket.sendall(struct.pack("Q", len(frame_data)))
            client_socket.sendall(frame_data)

            print(f"[App Video] Sent frame size: {len(frame_data)} bytes")

            if cv2.waitKey(1) == 13:  # If Enter key pressed, break streaming (optional)
                print("[App Video] Stream stopped by user input")
                break

        cap.release()
        cv2.destroyAllWindows()
        return 200
    except Exception as e:
        print(f"[App Video] Exception during streaming: {e}")
        cap.release()
        cv2.destroyAllWindows()
        return None

def do_connect(server_ip, server_port):
    while True:
        try:
            print(f"[App Video] Trying to connect to {server_ip}:{server_port}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            client_socket.connect((server_ip, server_port))
            print("[App Video] Connected to server")
            return client_socket
        except (socket.error, socket.timeout) as e:
            print(f"[App Video] Connection failed: {e}, retrying in 2 seconds...")
            time.sleep(2)
        except KeyboardInterrupt:
            print("[App Video] Connection attempts interrupted by user")
            raise

def main():
    server_ip = os.environ['ENV_SERVER_IP']
    server_port = int(os.environ['ENV_SERVER_PORT'])
    fps = int(os.environ['ENV_FPS'])
    width = int(os.environ['ENV_FRAME_WIDTH'])
    height = int(os.environ['ENV_FRAME_HEIGHT'])

    while True:
        client_socket = do_connect(server_ip, server_port)
        ret = do_stream(client_socket, fps, width, height)
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print(f"[App Video] Shutdown error: {e}")
        client_socket.close()

        if ret is None:
            print("[App Video] Connection lost, reconnecting...")
        else:
            print("[App Video] Streaming ended gracefully, reconnecting...")

        time.sleep(1)  # small delay before reconnect

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("[App Video] Client terminated by user")
