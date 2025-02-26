"""
This module implements a high level access to Fohhn Devices functions.
Once initialized with a communicator a device object can be used to access
all accessible data from a Fohhn device.
"""

from struct import unpack, pack
from .pyfohhn_fdcp import PyfohhnFdcpUdp


class PyFohhnDevice:
    pass

    def __init__(
        self, id=None, ip_address=None, port=2101, com_port=None, baud_rate=None
    ):
        self.id = id

        if ip_address and port:
            self.communicator = PyfohhnFdcpUdp(ip_address, port)
        elif com_port and baud_rate:
            self.communicator = None
        else:
            raise ValueError(
                "either ip_address and port or com_port and baud_rate required"
            )

        # todo scan for id if None

    def get_info(self):
        """
        Request device class and version
        """
        response = self.communicator.send_command(self.id, 0x20, 0x00, 0x00, b"\x01")
        return unpack(">HBBB", response)

    def set_volume(self, channel, vol, on, invert):
        """
        Set a channels volume (rounds the float volume to 0.1)
        """
        flags = 0
        if on:
            flags += 1
        if invert:
            flags += 2

        response = self.communicator.send_command(
            self.id, 0x87, channel, 1, pack(">hB", int(vol * 10), flags)
        )

    def get_volume(self, channel):
        """
        Get a channels volume
        """
        response = self.communicator.send_command(
            self.id, 0x0A, channel, 1, pack(">B", 0x87)
        )
        vol_int, flags = unpack(">hB", response)
        vol = float(vol_int) / 10
        on = bool(flags & 0x01)
        invert = bool(flags & 0x02)

        return vol, on, invert
