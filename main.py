from client import get_socket

if __name__ == "__main__":
    sock = get_socket(103)
    print("Getting Socket.")
    # Use the socket to send data
    message = "Hello over PPP from the library!"
    sock.send(message.encode())
    print(f"Sent: {message}")