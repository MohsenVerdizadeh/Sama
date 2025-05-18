import os
import socket
import sys
import logging
import time
from datetime import datetime

from dial import PPPDialer

# def setup_logging(log_file="/var/log/dial.log"):
#     logging.basicConfig(
#         filename=log_file,
#         level=logging.INFO,
#         format="%(asctime)s - %(levelname)s - %(message)s",
#     )
#
#
# def start_server(server_ip="192.168.10.100", port=12345):
#     try:
#         server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         server_socket.bind((server_ip, port))
#         server_socket.listen(1)
#         logging.info(f"Server listening on {server_ip}:{port}...")
#
#         client_socket, addr = server_socket.accept()
#         logging.info(f"Connected to {addr}")
#         return client_socket, server_socket
#     except Exception as e:
#         logging.error(f"Error starting server: {e}")
#         sys.exit(1)


# def main():
#     # setup_logging()
#     client_sock, server_sock = start_server()
#
#     try:
#         with open("data.txt", "w") as file:
#             while True:
#                 data = client_sock.recv(1024)
#                 if not data:
#                     break
#                 file.write(data.decode().strip())
#     except Exception as e:
#         print(f"Error during communication: {e}")
#     finally:
#         client_sock.close()
#         server_sock.close()
#         os.system("killall pppd")
#         logging.info("Server closed")


if __name__ == "__main__":
    dialer = PPPDialer()
    try:
        # Dial and establish PPP connection,Get a socket for communication
        client_sock, server_sock = dialer.dial_in()
        start_time = time.time()
        # Receive file size
        size = client_sock.recv(16).decode().strip()
        size = int(size)

        # Receive PDF data
        data = b''
        while len(data) < size:
            packet = client_sock.recv(size - len(data))
            if not packet:
                break
            data += packet

        # Save received PDF
        with open('data.pdf', 'wb') as f:
            f.write(data)

        end_time = time.time()
        print(f"Transfer Rate: {1.7 / (end_time - start_time)} KBps")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_sock.close()
        server_sock.close()
        os.system("killall pppd")
        # Clean up
        dialer.close()
