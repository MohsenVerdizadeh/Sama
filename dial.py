import logging
import subprocess
import socket
import sys
import time
import os
import signal
import db


def setup_logging(log_file="/var/log/dial.log"):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


class PPPDialer:
    def __init__(self, device=db.modem_path, baud=db.baud_rate, server_ip=db.server_ip,
                 client_ip=db.client_ip, phone_number=db.phone_number, username=db.client_username):
        self.device = device
        self.baud = baud
        self.server_ip = server_ip
        self.client_ip = client_ip
        self.phone_number = phone_number
        self.username = username
        self.pppd_path = "/etc/ppp/"
        self.pppd_process = None
        self.sock = None
        setup_logging()

    def dial_out(self):
        """Dial the server and establish the PPP connection."""

        logging.info("Start Checking dependencies")
        subprocess.run(["python3", "check_dependencies.py"])
        logging.info("Finish Checking dependencies")

        logging.info("Start dial out setup configs")
        self.dial_out_setup_configs()
        logging.info("Finish dial out setup configs")

        # Run pppd to dial
        pppd_cmd = [
            "pppd", "call", "dialout"
        ]
        try:
            self.pppd_process = subprocess.Popen(pppd_cmd, preexec_fn=os.setsid)
            logging.info("Dialing... Waiting for PPP connection.")
        except Exception as e:
            raise logging.error(f"Failed to start pppd: {e}")

        # Wait for ppp0 to come up
        for _ in range(40):  # Timeout after 30 seconds
            if self._check_ppp0():
                logging.info("PPP connection established on ppp0")
                return self.get_socket()
            time.sleep(1)
        raise logging.error("PPP connection failed to establish")

    def dial_out_setup_configs(self):
        """Create or verify the chat script."""
        script_content = f"""
                ABORT BUSY
                ABORT "NO CARRIER"
                "" ATZ
                OK ATDT{self.phone_number}
                CONNECT ""
        """
        with open(self.pppd_path + "chat-script", "w") as f:
            f.write(script_content.strip())
        os.chmod(self.pppd_path + "chat-script", 0o600)

        chap_secrets_content = f"{self.username} * {db.client_password} *"
        with open(self.pppd_path + "chap-secrets", "w") as f:
            f.write(chap_secrets_content.strip())

        options_content = f"""
        noauth  # Adjust if server requires auth
        lock
        crtscts
        connect "/usr/sbin/chat -v -f /etc/ppp/chat-script"
        {self.client_ip}:{self.server_ip}  # Client IP:Server IP
        """
        with open(self.pppd_path + "options", "w") as f:
            f.write(options_content.strip())

        dial_out_content = f"""
        {self.device}
        {self.baud}
        connect "/usr/sbin/chat -v -f /etc/ppp/chat-script"
        {self.client_ip}:{self.server_ip}
        user {self.username}
        debug
        """
        with open(self.pppd_path + "peers/dialout", "w") as f:
            f.write(dial_out_content.strip())

    def dial_in(self, server_ip="192.168.10.100", port=12345):
        logging.info("Start Checking dependencies")
        subprocess.run(["python3", "check_dependencies.py"])
        logging.info("Finish Checking dependencies")

        logging.info("Start dial in setup configs")
        self.dial_in_setup_configs()
        logging.info("Finish dial in setup configs")

        logging.info("Waiting for dial in ....")
        while True:
            if self._check_ppp0():
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

    def dial_in_setup_configs(self):
        pppd_path = "/etc/ppp/"

        chap_secrets_content = f"{db.client_username} * {db.client_password} {db.client_ip}"
        with open(pppd_path + "chap-secrets", "w") as f:
            f.write(chap_secrets_content.strip())

        options_content = f"""
                    auth          # Require authentication
                    +chap         # Use CHAP
                    -pap          # Disable PAP
                    lock          # Lock the serial device
                    {db.server_ip}:{db.client_ip}  # Server:Client IPs
                    debug         # Enable detailed logging
                    """
        with open(pppd_path + "options", "w") as f:
            f.write(options_content.strip())

    def _check_ppp0(self):
        """Check if ppp0 interface is up with the correct IP."""
        try:
            output = subprocess.check_output(["ip", "addr", "show", "ppp0"], stderr=subprocess.DEVNULL).decode()
            return self.client_ip in output
        except subprocess.CalledProcessError:
            return False

    def get_socket(self, port=12345):
        """Return a connected socket to the server over ppp0."""
        if not self._check_ppp0():
            raise logging.error("PPP connection not active")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # time.sleep(20)
            self.sock.connect((self.server_ip, port))
            logging.info(f"Socket connected to {self.server_ip}:{port}")
            return self.sock
        except Exception as e:
            self.sock.close()
            raise logging.error(f"Failed to connect socket: {e}")

    def close(self):
        """Close the socket and terminate the PPP connection."""
        # os.system("killall pppd")
        # subprocess.run(["python3", "check_dependencies.py"])
        if self.sock:
            self.sock.close()
            logging.info("Socket closed")
        if self.pppd_process:
            os.killpg(os.getpgid(self.pppd_process.pid), signal.SIGTERM)
            self.pppd_process.wait()
            logging.info("PPP connection closed")
        self.pppd_process = None
        self.sock = None

    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.close()


def get_socket(phone_number=db.phone_number):
    dialer = PPPDialer(phone_number=phone_number)
    # Dial and establish PPP connection
    dialer.dial_out()

    # Get a socket for communication
    sock = dialer.get_socket(port=12345)

    return sock
