"""
Communication module to interact with Fohhn devices usind UDP or serial.
"""

import socket


class PyfohhnFdcp:

    START_BYTE = 0xF0
    CONTROL_BYTE = 0xFF
    ESCAPED_START_BYTE = 0x00
    ESCAPED_CONTROL_BYTE = 0x01

    @classmethod
    def _escape_data(cls, data):
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
            else:
                if byte == cls.CONTROL_BYTE:
                    escape_sequence_detected = True
                else:
                    unescaped_data.append(byte)

        return unescaped_data


class PyfohhnFdcpUdp(PyfohhnFdcp):

    def __init__(self, ip_address, port=2101):
        super().__init__()
        self.ip_address = ip_address
        self.port = port

    def send_command(self, id, command, msb, lsb, data):
        """
        Escape and send a binary FDCP command and wait for the response.
        """

        # calc actual payload length - 0 means 256 bytes
        if len(data) > 0 and len(data) < 256:
            length = len(data)
        elif length == 256:
            length = 0
        else:
            raise ValueError("payload length must be in range from 1 to 256")

        escaped_command = bytearray(self.START_BYTE)
        escaped_command += self._escape_data(bytearray([id, length, command, msb, lsb]))
        escaped_command += self._escape_data(data)

        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        sock.bind((socket.INADDR_ANY, self.port))
        sock.settimeout(1)

        # send command to device
        sock.sendto(escaped_command, (self.ip_address, self.port))

        response = sock.recv(600)

        if response:
            return self._unescape_data(response[:-2])
        return None
