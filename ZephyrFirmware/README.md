# Find My Device ESP32 Firmware

This code enables you to use a Zephyr-supported BLE device as a custom Google Find My Device tracker.
It should support any board/chip with a BLE radio that is supported in Zephyr, for example:

 - Nordic nRF5x
 - Silicon EFR32BG22
 - ST BlueNRG-LP
 - ESP32
 - Quectel BC68-GV
 - TTGO T-BEAM


## Installation

Follow the [official instructions](https://docs.zephyrproject.org/latest/develop/getting_started/index.html#install-dependencies) to install Zephyr's dependencies.

Create a virtual environment in this directory and install `west`:

```
python3 -m venv .venv
source .venv/bin/activate
pip install west
```

Initialize the Zephyr workspace:

```
west init -l app
west update --narrow
```

Finalize the setup of `west`:

```
west zephyr-export
west packages pip --install
```

Install the Zephyr SDK following the [official instructions](https://docs.zephyrproject.org/latest/develop/getting_started/index.html#install-the-zephyr-sdk)

## Building

To build the app for the nRF52840dk:

```
west build -p -b nrf52840dk/nrf52840 app
```

To build with UART logging:

```
west build -p -b nrf52840dk/nrf52840 app -- -DEXTRA_CONF_FILE=logging.conf
```

## Known Issues

See [the README](../ESP32Firmware/README.md) for ESP32-based trackers (also applies here).
