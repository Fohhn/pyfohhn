"""
Communication module to interact with Fohhn devices usind UDP or serial.
"""

import socket
import serial


class PyfohhnFdcp:

    START_BYTE = 0xF0
    CONTROL_BYTE = 0xFF
    ESCAPED_START_BYTE = 0x00
    ESCAPED_CONTROL_BYTE = 0x01

    @classmethod
    def _escape_data(cls, data):
        """
        Escape binary data to be sent to a device (escape start and control byte)
        """
        escaped_data = bytearray()

        for byte in data:
            if byte == cls.START_BYTE:
                escaped_data.append(cls.CONTROL_BYTE)
                escaped_data.append(cls.ESCAPED_START_BYTE)
            elif byte == cls.CONTROL_BYTE:
                escaped_data.append(cls.CONTROL_BYTE)
                escaped_data.append(cls.ESCAPED_CONTROL_BYTE)
            else:
                escaped_data.append(byte)

        return escaped_data

    @classmethod
    def _unescape_data(cls, data):
        """
        Unescape data received from a device
        """
        unescaped_data = bytearray()
        escape_sequence_detected = False

        for byte in data:
            if escape_sequence_detected:
                if byte == cls.ESCAPED_START_BYTE:
                    unescaped_data.append(cls.START_BYTE)
                elif byte == cls.ESCAPED_CONTROL_BYTE:
                    unescaped_data.append(cls.CONTROL_BYTE)
                else:
                    return None
                escape_sequence_detected = False
            else:
                if byte == cls.CONTROL_BYTE:
                    escape_sequence_detected = True
                else:
                    unescaped_data.append(byte)

        return unescaped_data

    def _prepare_command(self, id, command, msb, lsb, data):
        """
        Assemble and escape a command
        """
        # calc actual payload length - 0 means 256 bytes
        if len(data) > 0 and len(data) < 256:
            length = len(data)
        elif len(data) == 256:
            length = 0
        else:
            raise ValueError("payload length must be in range from 1 to 256")

        escaped_command = bytearray([self.START_BYTE])
        escaped_command += self._escape_data(bytearray([id, length, command, msb, lsb]))
        escaped_command += self._escape_data(data)

        return escaped_command

    def _send_command(self, escaped_command):
        """
        Abstract method to actually send data to the device
        """
        raise NotImplementedError()

    def send_command(self, id, command, msb, lsb, data, retries=2):
        """
        Escape and send a binary FDCP command and wait for the response.
        """
        escaped_command = self._prepare_command(id, command, msb, lsb, data)

        for i in range(retries + 1):
            response = self._send_command(escaped_command)
            if response:
                return self._unescape_data(response[:-2])

        return None


class PyfohhnFdcpUdp(PyfohhnFdcp):
    """
    Communication class to communicate with Fohhn devices using UDP
    """

    def __init__(self, ip_address, port=2101):
        super().__init__()
        self.ip_address = ip_address
        self.port = port
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.sock.settimeout(0.1)

    def _send_command(self, escaped_command):
        """
        Send a pre-escaped command via UDP
        """
        # send command to device
        self.sock.sendto(escaped_command, (self.ip_address, self.port))

        try:
            response = self.sock.recv(600)
        except TimeoutError:
            response = None

        return response

    def send_text_command(self, command, retries=2):
        """
        Send a text command to a device and return the response
        """

        for i in range(retries + 1):
            with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as sock:
                sock.settimeout(0.1)

                # send command to device
                sock.sendto(command.encode("ASCII"), (self.ip_address, self.port))

                try:
                    response = sock.recv(600)
                    return response.decode("ASCII")
                except TimeoutError:
                    response = None
        return response


class PyfohhnFdcpSerial(PyfohhnFdcp):
    """
    Communication class to communicate with Fohhn devices using a serial port
    """

    def __init__(self, com_port=None, baud_rate=None):
        super().__init__()
        self.com_port = com_port
        self.baud_rate = baud_rate

    def _send_command(self, escaped_command):
        """
        Send a pre-escaped command via serial
        """
        response = bytearray()

        with serial.Serial(self.com_port, self.baud_rate, timeout=0.1) as ser:
            ser.write(escaped_command)

            while True:
                data = ser.read(1)

                if data:
                    response.append(data[0])

                    if response[-1] == self.START_BYTE:
                        break
                else:
                    return None

        return response
