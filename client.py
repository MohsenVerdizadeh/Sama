import subprocess
import socket
import time
import os
import signal
import db


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

    def start_connection(self):
        """Dial the server and establish the PPP connection."""
        # Ensure chat script exists
        subprocess.run(["python3", "install_pkgs.py"])
        self._setup_configs()

        # Run pppd to dial
        pppd_cmd = [
             "pppd", "call", "dialout"
        ]
        try:
            self.pppd_process = subprocess.Popen(pppd_cmd, preexec_fn=os.setsid)
            print("Dialing... Waiting for PPP connection.")
        except Exception as e:
            raise RuntimeError(f"Failed to start pppd: {e}")

        # Wait for ppp0 to come up
        for _ in range(40):  # Timeout after 30 seconds
            if self._check_ppp0():
                print("PPP connection established on ppp0")
                return True
            time.sleep(1)
        raise RuntimeError("PPP connection failed to establish")

    def _setup_configs(self):
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

    def _check_ppp0(self):
        """Check if ppp0 interface is up with the correct IP."""
        try:
            output = subprocess.check_output(["ip", "addr", "show", "ppp0"]).decode()
            return self.client_ip in output
        except subprocess.CalledProcessError:
            return False

    def get_socket(self, port=12345):
        """Return a connected socket to the server over ppp0."""
        if not self._check_ppp0():
            raise RuntimeError("PPP connection not active")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            time.sleep(20)
            self.sock.connect((self.server_ip, port))
            print(f"Socket connected to {self.server_ip}:{port}")
            return self.sock
        except Exception as e:
            self.sock.close()
            raise RuntimeError(f"Failed to connect socket: {e}")

    def close(self):
        """Close the socket and terminate the PPP connection."""
        subprocess.run(["python3", "install_pkgs.py"])
        if self.sock:
            self.sock.close()
            print("Socket closed")
        if self.pppd_process:
            os.killpg(os.getpgid(self.pppd_process.pid), signal.SIGTERM)
            self.pppd_process.wait()
            print("PPP connection closed")
        self.pppd_process = None
        self.sock = None

    def __del__(self):
        """Ensure cleanup on object destruction."""
        self.close()
