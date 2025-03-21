import os
import socket
import sys
import logging


def setup_logging(log_file="/var/log/ppp_server.log"):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def start_server(server_ip="192.168.10.100", port=12345):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((server_ip, port))
        server_socket.listen(1)
        logging.info(f"Server listening on {server_ip}:{port}...")

        client_socket, addr = server_socket.accept()
        logging.info(f"Connected to {addr}")
        return client_socket, server_socket
    except Exception as e:
        logging.error(f"Error starting server: {e}")
        sys.exit(1)


def main():
    setup_logging()
    client_sock, server_sock = start_server()

    try:
        while True:
            data = client_sock.recv(1024)
            if not data:
                break
            logging.info(f"Received: {data.decode().strip()}")
    except Exception as e:
        logging.error(f"Error during communication: {e}")
    finally:
        client_sock.close()
        server_sock.close()
        os.system("killall pppd")
        logging.info("Server closed")


if __name__ == "__main__":
    main()
