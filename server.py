import os
import socket
import sys

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = "192.168.10.100"
    port = 12345
    server_socket.bind((server_ip, port))
    server_socket.listen(1)
    print(f"Server listening on {server_ip}:{port}...")

    client_socket, addr = server_socket.accept()
    print(f"Connected to {addr}")
    return client_socket, server_socket

if __name__ == "__main__":
    # Redirect output to log file
    sys.stdout = open("/var/log/ppp_server.log", "a")
    sys.stderr = sys.stdout

    client_sock, server_sock = start_server()
    try:
        while True:
            data = client_sock.recv(1024)
            if not data:
                break
            print(f"Received: {data.decode()}")
    finally:
        client_sock.close()
        server_sock.close()
        os.system("killall pppd")
        print("Server closed")