import cv2
import socket
import pickle
import struct
import os

def receive_frames(client_socket):
    """Receive frames from the server."""
    data = b''
    payload_size = struct.calcsize("Q")

    while True:
        try:
            # Retrieve the message size
            print('Retrieve message size...')
            while len(data) < payload_size:
                packet = client_socket.recv(4 * 1024)  # 4KB chunk
                if not packet:  # If no packet is received, the connection might be closed
                    raise ConnectionResetError("No packet received, connection may be closed.")
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]

            # Unpack the message size
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            # Get the full frame data
            print('Get the full frame data...')
            while len(data) < msg_size:
                packet = client_socket.recv(4 * 1024)
                if not packet:
                    raise ConnectionResetError("No packet received, connection lost.")
                data += packet

            frame_data = data[:msg_size]
            data = data[msg_size:]

            # Decode the frame
            frame = pickle.loads(frame_data)

            # Display the frame
            print('Getting data=' + str(frame))
            if frame is None:
                raise ConnectionResetError

            # Check if the user pressed 'q' to quit the video stream
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except (ConnectionResetError, socket.timeout, socket.error) as e:
            print(f"Connection error: {e}")
            return

def connect_to_server(ip,port):
    """Attempt to connect to the server."""
    while True:
        try:
            print("Trying to connect to ip="+str(ip)+',port='+str(port))
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ip, port))
            print("Connected to server")
            return client_socket
        except (socket.error,socket.timeout):
            print("Server unavailable, retrying...")


def main(ip,port):
    while True:
        client_socket = connect_to_server(ip=ip,port=port)
        receive_frames(client_socket)
        client_socket.close()
        print("Reconnecting to server...")

if __name__ == "__main__":
    try:
        _server_ip = os.environ['ENV_SERVER_IP']
        _server_port = int(os.environ['ENV_SERVER_PORT'])
        main(_server_ip,_server_port)
    except KeyboardInterrupt:
        print("Client terminated by user.")
    finally:
        cv2.destroyAllWindows()

