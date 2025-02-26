"""
This module implements a high level access to Fohhn Devices functions.
Once initialized with a communicator a device object can be used to access
all accessible data from a Fohhn device.
"""

from struct import unpack, pack
from .pyfohhn_fdcp import PyfohhnFdcpUdp


class PyFohhnCommands:

    LOAD_PRESET = 0x05
    GET_PRESET_NAME = 0x8E
    READBACK = 0x0A
    SET_VOL = 0x87
    SET_RVOL = 0x96
    SET_STANDBY = 0x0C
    SET_ROUTE = 0x81
    GET_INFO = 0x20
    GET_CONTROLS = 0x07
    GET_SPEAKER = 0x22
    SET_LIGHT = 0x0D
    SET_DYNAMIC = 0x83
    SET_DYNAMIC_GAIN = 0x84
    SET_DYNAMIC_TIME = 0x85
    SET_EQ = 0x80
    SET_GATE = 0x89
    SET_GATE_TIME = 0x8A
    SET_XOVER = 0x82
    SET_DELAY = 0x86
    SET_SPEAKER = 0x21


class PyFohhnDevice:

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

    def load_preset(self, preset_nr):
        """
        Load a specified preset
        """
        _response = self.communicator.send_command(
            self.id, PyFohhnCommands.LOAD_PRESET, 0x01, preset_nr, b"\x00"
        )

    def set_speaker(self, channel, speaker_nr):
        """
        Load a speaker preset to a channel
        """
        _response = self.communicator.send_command(
            self.id, PyFohhnCommands.SET_SPEAKER, channel, speaker_nr, b"\x00"
        )

    def get_preset(self):
        """
        Get the loaded preset name
        """
        response = self.communicator.send_command(
            self.id, PyFohhnCommands.GET_PRESET_NAME, 0x01, 0x00, b"\x00"
        )
        return response.decode("ASCII")

    def get_speaker(self, channel):
        """
        Get the number and name of a loaded speaker preset by channel
        """
        response = self.communicator.send_command(
            self.id, PyFohhnCommands.GET_SPEAKER, channel, 0x00, b"\x00"
        )
        # todo - is it correct to receive the first 20 bytes?
        return response[20], response[22:38].decode("ASCII")

    def set_volume(self, channel, vol, on, invert):
        """
        Set a channels volume (rounds the float volume to 0.1)
        """
        flags = 0
        if on:
            flags += 1
        if invert:
            flags += 2

        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_VOL,
            channel,
            1,
            pack(">hB", int(vol * 10), flags),
        )

    def set_relative_volume(self, channel, rel_vol):
        """
        Set a channels volume relative to the active volume (rounds the float volume to 0.1)
        """
        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_RVOL,
            channel,
            1,
            pack(">hB", int(rel_vol * 10), 0x01),
        )

    def get_volume(self, channel):
        """
        Get a channels volume
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            channel,
            1,
            pack(">B", PyFohhnCommands.SET_VOL),
        )
        vol_int, flags = unpack(">hB", response)
        vol = float(vol_int) / 10
        on = bool(flags & 0x01)
        invert = bool(flags & 0x02)

        return vol, on, invert

    def set_routing_volume(self, channel_out, channel_in, vol, on, invert):
        """
        Set the routing volume from a channel to a channel
        """
        flags = 0
        if on:
            flags += 1
        if invert:
            flags += 2

        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_ROUTE,
            channel_out,
            channel_in,
            pack(">hB", int(vol * 10), flags),
        )

    def get_routing_volume(self, channel_out, channel_in):
        """
        Get the routing volume from a channel to a channel
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            channel_out,
            channel_in,
            pack(">B", PyFohhnCommands.SET_ROUTE),
        )
        vol_int, flags = unpack(">hB", response)
        vol = float(vol_int) / 10
        on = bool(flags & 0x01)
        invert = bool(flags & 0x02)

        return vol, on, invert

    def set_mute(self, channel, on):
        """
        Enables/disables the mute status of a channel without affecting the set volume
        """
        flags = 0
        if on:
            flags += 5

        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_RVOL,
            channel,
            1,
            pack(">hB", 0, flags),
        )

    def get_mute(self, channel):
        """
        Returns if a channel is turned on
        """
        _vol, on, _invert = response = self.get_volume(channel)
        return on

    def set_standby(self, on):
        """
        Enables or disables the standby of a device
        """
        flags = 0
        if on:
            flags += 1

        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_STANDBY,
            0,
            0,
            pack(">B", flags),
        )

    def get_standby(self):
        """
        Get the current standby state (if the device is turned on)
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            0,
            0,
            pack(">B", PyFohhnCommands.SET_STANDBY),
        )
        return bool(response[0])

    def get_info(self):
        """
        Request device class and version
        """
        response = self.communicator.send_command(
            self.id, PyFohhnCommands.GET_INFO, 0x00, 0x00, b"\x01"
        )
        return unpack(">HBBB", response)

    def get_controls(self):
        """
        Request device controls (protect bits)
        """
        response = self.communicator.send_command(
            self.id, PyFohhnCommands.GET_CONTROLS, 0x00, 0x00, b"\x01"
        )
        return response[0]

    def get_temperature(self):
        """
        Request the device temperature
        """
        response = self.communicator.send_command(
            self.id, PyFohhnCommands.GET_CONTROLS, 0x00, 0x00, b"\x01"
        )
        return float(unpack(">h", response[1:3])[0]) / 10

    def set_light(self, on, sign):
        """
        Control the front LED of the device
        """
        flags = 0
        if on:
            flags += 1
        if sign:
            flags += 2

        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_LIGHT,
            0,
            0,
            pack(">B", flags),
        )

    def get_light(self):
        """
        Get the current state of the front LED of the device
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            0,
            0,
            pack(">B", PyFohhnCommands.SET_LIGHT),
        )
        # todo does not work
        on = bool(response[0] & 0x01)
        sign = bool(response[0] & 0x02)

        return on, sign

    def set_eq(self, channel, filter_nr, freq, q, gain, on):
        """
        Set equalizer values to one filter of a channel - float values will be rounded
        """
        flags = 0
        if on:
            flags += 1

        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_EQ,
            channel,
            filter_nr,
            pack(">HHhB", int(freq), int(q * 10), int(gain * 10), flags),
        )

    def get_eq(self, channel, filter_nr):
        """
        Get equalizer values from one filter of a channel
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            channel,
            filter_nr,
            pack(">B", PyFohhnCommands.SET_EQ),
        )

        freq_int, q_int, gain_int, flags = unpack(">HHhB", response)
        freq = float(freq_int)
        q = float(q_int) / 10
        gain = float(gain_int) / 10
        on = bool(flags & 0x01)

        return freq, q, gain, on

    def set_xover(self, channel, filter_nr, freq, on):
        """
        Set the crossover of a channel (filter_nr: 1: HP, 1: LP)
        """
        flags = 0
        if on:
            flags += 1

        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_XOVER,
            channel,
            filter_nr,
            pack(">HBB", int(freq), filter_nr, flags),
        )

    def get_xover(self, channel, filter_nr):
        """
        Get the crossover of a channel (filter_nr: 1: HP, 1: LP)
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            channel,
            filter_nr,
            pack(">B", PyFohhnCommands.SET_XOVER),
        )

        freq_int, _nr, flags = unpack(">HBB", response)
        freq = float(freq_int)
        on = bool(flags & 0x01)

        return freq, on

    def set_delay(self, channel, delay, on):
        """
        Sets the delay [s] to a channel
        """
        flags = 0
        if on:
            flags += 1

        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_DELAY,
            channel,
            1,
            pack(">HB", int(delay * 100000), flags),
        )

    def get_delay(self, channel):
        """
        Requests the delay [s] of a channel
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            channel,
            1,
            pack(">B", PyFohhnCommands.SET_DELAY),
        )

        delay_int, flags = unpack(">HB", response)
        delay = float(delay_int) / 100000
        on = bool(flags & 0x01)

        return delay, on

    def set_gate(self, channel, threshold, on):
        """
        Sets the gate threshold to a channel
        """
        flags = 0
        if on:
            flags += 1

        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_GATE,
            channel,
            1,
            pack(">hB", int(threshold * 10), flags),
        )

    def get_gate(self, channel):
        """
        Requests the gate threshold of a channel
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            channel,
            1,
            pack(">B", PyFohhnCommands.SET_GATE),
        )

        gate_int, flags = unpack(">hB", response)
        gate = float(gate_int) / 10
        on = bool(flags & 0x01)

        return gate, on

    def set_gate_time(self, channel, time):
        """
        Sets the gate hold time[s] to a channel
        """
        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_GATE_TIME,
            channel,
            1,
            pack(">h", int(time)),
        )

    def get_gate_time(self, channel):
        """
        Requests the gate hold time[s] of a channel
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            channel,
            1,
            pack(">B", PyFohhnCommands.SET_GATE_TIME),
        )

        return unpack(">H", response[:2])[0]

    def set_dynamics(self, channel, lim, comp, ratio, on):
        """
        Sets the dynamics thresholds and ratio to a channel
        """
        flags = 0
        if on:
            flags += 1

        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_DYNAMIC,
            channel,
            1,
            pack(">hhHB", int(lim * 10), int(comp * 10), int(ratio * 10), flags),
        )

    def get_dynamics(self, channel):
        """
        Requests the dynamics thresholds and ratio of a channel
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            channel,
            1,
            pack(">B", PyFohhnCommands.SET_DYNAMIC),
        )

        lim_int, comp_int, ratio_int, flags = unpack(">hhHB", response)
        lim = float(lim_int) / 10
        comp = float(comp_int) / 10
        ratio = float(ratio_int) / 10
        on = bool(flags & 0x01)

        return lim, comp, ratio, on
    
    def set_dynamics_time(self, channel, attack, release):
        """
        Sets the dynamics time constants[s] to a channel
        """
        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_DYNAMIC_TIME,
            channel,
            1,
            pack(">HH", int(attack * 10000), int(release * 10000)),
        )

    def get_dynamics_time(self, channel):
        """
        Requests the dynamics time constants[s] of a channel
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            channel,
            1,
            pack(">B", PyFohhnCommands.SET_DYNAMIC_TIME),
        )

        attack_int, release_int = unpack(">HH", response)
        attack = float(attack_int) / 10000
        release = float(release_int) / 10000

        return attack, release

    def set_post_dynamics_gain(self, channel, vol):
        """
        Set the post dynamics gain (rounds the float volume to 0.1)
        """
        _response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.SET_DYNAMIC_GAIN,
            channel,
            1,
            pack(">hB", int(vol * 10), 1),
        )

    def get_post_dynamics_gain(self, channel):
        """
        Get the post dynamic gain of a channel
        """
        response = self.communicator.send_command(
            self.id,
            PyFohhnCommands.READBACK,
            channel,
            1,
            pack(">B", PyFohhnCommands.SET_DYNAMIC_GAIN),
        )
        vol_int, _flags = unpack(">hB", response)
        vol = float(vol_int) / 10

        return vol
