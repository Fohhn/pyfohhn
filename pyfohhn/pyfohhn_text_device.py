"""
This module implements a high level access to Fohhn Devices functions using the´
UDP textprotocol
"""

import re
from .pyfohhn_fdcp import PyfohhnFdcpUdp
from .pyfohhn_device import PyFohhnCommands


class PyFohhnTextDevice:
    """
    Device communication class to be used to exchange data with a device using UDP text protocol.
    """

    MAX_ID = 254

    def __init__(self, id=None, ip_address=None, port=2101):
        self.id = id

        if not ip_address:
            raise ValueError("IP address is required")

        self.communicator = PyfohhnFdcpUdp(ip_address, port)

        # scan for devices - use first found device ID
        if self.id is None:
            for i in range(1, self.MAX_ID):
                response = self.communicator.send_command(
                    i, PyFohhnCommands.GET_INFO, 0x00, 0x00, b"\x01", retries=0
                )
                if response:
                    self.id = i
                    break
            else:
                raise ValueError("No device found - please check connection")

    def load_preset(self, preset_nr):
        """
        Load a specified preset
        """
        _response = self.communicator.send_text_command(
            f"SET PRESET {self.id} {preset_nr}\r\n"
        )

    def get_preset(self):
        """
        Get the loaded preset number and name
        """
        response = self.communicator.send_text_command(f"GET PRESET {self.id}\r\n")
        match = re.match(r"(\d+)\s(.*)", response)
        return int(match.group(1)), match.group(2)

    def set_volume(self, channel, vol, on, invert):
        """
        Set a channels volume (rounds the float volume to 0.1)
        """
        _response = self.communicator.send_text_command(
            f"SET VOL {self.id} {channel} {int(vol * 10)} {1 if on else 0} {1 if invert else 0}\r\n"
        )

    def set_relative_volume(self, channel, rel_vol):
        """
        Set a channels volume relative to the active volume (rounds the float volume to 0.1)
        """
        _response = self.communicator.send_text_command(
            f"SET RVOL {self.id} {channel} {int(rel_vol * 10)}\r\n"
        )

    def get_volume(self, channel):
        """
        Get a channels volume
        """
        response = self.communicator.send_text_command(
            f"GET VOL {self.id} {channel}\r\n"
        )
        match = re.match(r"([\-]?\d+)\s(\d+)\s(\d+)", response)
        return float(match.group(1)) / 10, match.group(2) == "1", match.group(3) == "1"

    def set_routing_volume(self, channel_out, channel_in, vol, on, invert):
        """
        Set the routing volume from a channel to a channel
        """
        _response = self.communicator.send_text_command(
            f"SET ROUTING {self.id} {channel_out} {channel_in} {int(vol * 10)} {1 if on else 0} {1 if invert else 0}\r\n"
        )

    def get_routing_volume(self, channel_out, channel_in):
        """
        Get the routing volume from a channel to a channel
        """
        response = self.communicator.send_text_command(
            f"GET ROUTING {self.id} {channel_out} {channel_in}\r\n"
        )
        match = re.match(r"([\-]?\d+)\s(\d+)\s(\d+)", response)
        return float(match.group(1)) / 10, match.group(2) == "1", match.group(3) == "1"

    def set_mute(self, channel, on):
        """
        Enables/disables the mute status of a channel without affecting the set volume
        """
        _response = self.communicator.send_text_command(
            f"SET MUTE {self.id} {channel} {1 if on else 0}\r\n"
        )

    def get_mute(self, channel):
        """
        Returns if a channel is turned on
        """
        response = self.communicator.send_text_command(
            f"GET MUTE {self.id} {channel}\r\n"
        )
        return response == "1"

    def set_standby(self, on):
        """
        Enables or disables the standby of a device
        """
        _response = self.communicator.send_text_command(
            f"SET STANDBY {self.id} {1 if on else 0}\r\n"
        )

    def get_standby(self):
        """
        Get the current standby state (if the device is turned on)
        """
        response = self.communicator.send_text_command(f"GET STANDBY {self.id}\r\n")
        return response == "1"

    def get_info(self):
        """
        Request device class and version
        """
        response = self.communicator.send_text_command(f"GET INFO {self.id}\r\n")
        match = re.match(r"([0-9A-Fa-f]{4})\s(\d+)\.(\d+)\.(\d+)", response)
        return (
            int(match.group(1), 16),
            int(match.group(2)),
            int(match.group(3)),
            int(match.group(4)),
        )

    def get_controls(self):
        """
        Request device controls (protect bits)
        """
        response = self.communicator.send_text_command(f"GET STAT {self.id}\r\n")
        return int(response.replace(" ", ""), 2)
