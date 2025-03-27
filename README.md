# pyfohhn

Python library to interact with Fohhn Speakers


Pyfohhn uses either FDCP (Fohhn DSP control protocol - binary format - the
native format Fohhn Audio Soft is using) or a UDP Text protocol with limited
commands.

FDCP can be used with either a serial connection (com port / RS485) or UDP.


## Installation

The package can be simply installed from PyPi:

```
pip install pyfohhn
```

## Example

```
from pyfohhn import PyFohhnDevice

# Open connection to a device that has ID=1 via UDP
dev = PyFohhnDevice(id=1, ip_address="192.168.0.164")

# Read and print device class and version
dev_class, ver_major, ver_minor, ver_micro = dev.get_info()
print(f"{dev_class:04x}, {ver_major}.{ver_minor}.{ver_micro}")

# Change volume settings of channel 1
dev.set_volume(1, -5, True, False)

# Get and print current volume settings of channel 1
print(dev.get_volume(1))

```

The functions are quite self explaining - just check the docstrings.

## License

pyfohhn is licensed under the [MIT License](https://opensource.org/licenses/MIT), see [LICENSE](LICENSE) for more information.
