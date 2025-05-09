from dial import PPPDialer
from datetime import datetime

if __name__ == "__main__":
    dialer = PPPDialer()
    try:
        # Dial and establish PPP connection,Get a socket for communication
        sock = dialer.dial_out()
        print(f"Start sending PDF File.{datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]}")

        # Use the socket to send data
        # Read PDF file
        with open('data.pdf', 'rb') as f:  # Replace with your PDF path
            data = f.read()

        # Send file size first
        sock.send(str(len(data)).encode().ljust(16))

        # Send PDF data
        sock.sendall(data)
        print(f"Sent PDF File.{datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        dialer.close()