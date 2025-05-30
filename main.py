from client import PPPDialer

if __name__ == "__main__":
    dialer = PPPDialer()
    try:
        # Dial and establish PPP connection
        dialer.start_connection()

        # Get a socket for communication
        sock = dialer.get_socket(port=12345)

        # Use the socket to send data
        message = "Hello over PPP from the library!"
        sock.send(message.encode())
        print(f"Sent: {message}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        dialer.close()