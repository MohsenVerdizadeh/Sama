from client import get_socket

if __name__ == "__main__":
    sock = get_socket(103)
    # Use the socket to send data
    message = "Hello over PPP from the library!"
    sock.send(message.encode())
    print(f"Sent: {message}")

    # Example: Send a file
    with open("sample.txt", "rb") as f:
        while (data := f.read(1024)):
            sock.send(data)
    print("File sent")