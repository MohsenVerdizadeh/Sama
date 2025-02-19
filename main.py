from PyQt6.QtSerialPort import QSerialPort
from PyQt6.QtCore import QIODevice, QTimer
from PyQt6.QtWidgets import QApplication
import sys

class Dialer:
    def __init__(self, port_name="COM4", baud_rate=9600, phone_number="09190868330"):
        self.serial = QSerialPort()
        self.serial.setPortName(port_name)
        self.serial.setBaudRate(baud_rate)
        self.serial.readyRead.connect(self.read_response)

        if self.serial.open(QIODevice.OpenModeFlag.ReadWrite):
            print(f"Connected to {port_name}")
            self.dial(phone_number)
        else:
            print("Failed to open serial port")

    def dial(self, number):
        """Dial a phone number using AT commands."""
        command = f"ATD{number};\r"
        self.serial.write(command.encode())
        print(f"Dialing {number}...")

    def read_response(self):
        """Read responses from the modem."""
        response = self.serial.readAll().data().decode().strip()
        print("Modem Response:", response)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialer = Dialer(port_name="COM3", phone_number="123456789")
    sys.exit(app.exec())
