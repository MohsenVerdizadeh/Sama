import subprocess
import sys
import os

import db


def check_root():
    """Ensure the script runs with root privileges."""
    if os.geteuid() != 0:
        print("This script requires root privileges. Please run with sudo.")
        sys.exit(1)


def is_package_installed(package):
    """Check if a package is installed using dpkg."""
    try:
        subprocess.check_call(["dpkg", "-l", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def install_package(package):
    """Install a specified package if not already installed."""
    if is_package_installed(package):
        print(f"'{package}' is already installed.")
        return

    print(f"Installing '{package}'...")
    try:
        subprocess.check_call(["apt", "install", "-y", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"'{package}' installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install '{package}': {e}")
        sys.exit(1)

    # Verify installation
    if is_package_installed(package):
        print(f"Verification: '{package}' is installed.")
    else:
        print(f"Verification failed: '{package}' not installed.")
        sys.exit(1)


def install_ppp_tools():
    """Install both ppp (pppd) and mgetty."""
    # # Update package list
    # print("Updating package list...")
    # try:
    #     subprocess.check_call(["apt", "update"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # except subprocess.CalledProcessError as e:
    #     print(f"Failed to update package list: {e}")
    #     sys.exit(1)

    # Install ppp (includes pppd and chat)
    install_package("ppp")

    # Install mgetty
    install_package("mgetty")


def setup_configs():
    mgetty_path = "/etc/mgetty/"
    mgetty_login_content = f"""
    /AutoPPP/ - a_ppp /usr/sbin/pppd auth +chap -pap debug logfile /var/log/pppd.log  
    PORT01="{db.modem_path}"
    INIT01="AT&F&D2&C1"
    B115200="AT&F&D2&C1"
    """
    with open(mgetty_path + "login.config", "w") as f:
        f.write(mgetty_login_content.strip())

    mgetty_config_content = f"""
        port {db.modem_path}
        speed {db.baud_rate}
        debug 9
        data-only y
        """
    with open(mgetty_path + "mgetty.config", "w") as f:
        f.write(mgetty_config_content.strip())

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

    current_directory = os.getcwd()

    ip_up_content=f"""
    # Check if this is ppp0 coming up
if [ "$1" = "ppp0" ]; then
    # Path to your ppp_server.py
    SERVER_SCRIPT="{current_directory}/server.py"
    # Run the Python script in the background
    /usr/bin/python3 "$SERVER_SCRIPT" &>> /var/log/ppp_server.log &
fi
    """
    with open(pppd_path+"ip-up","a")as file:
        file.write(ip_up_content)

    os.system("sudo touch /var/log/ppp_server.log")
    os.system("sudo chmod 640 /var/log/ppp_server.log")
    os.system("sudo chown root:adm /var/log/ppp_server.log")

if __name__ == "__main__":
    check_root()
    install_ppp_tools()
    setup_configs()
