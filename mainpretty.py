import asyncio
import argparse
import time
import sys
import signal
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError


def print_intro():
    print("""

██████╗  ██████╗ ██╗  ██╗    ██████╗ ██╗██████╗ ██████╗ ███████╗██████╗ 
██╔══██╗██╔════╝ ╚██╗██╔╝    ██╔══██╗██║██╔══██╗██╔══██╗██╔════╝██╔══██╗
██████╔╝██║  ███╗ ╚███╔╝     ██████╔╝██║██████╔╝██████╔╝█████╗  ██████╔╝
██╔══██╗██║   ██║ ██╔██╗     ██╔══██╗██║██╔═══╝ ██╔═══╝ ██╔══╝  ██╔══██╗
██████╔╝╚██████╔╝██╔╝ ██╗    ██║  ██║██║██║     ██║     ███████╗██║  ██║
╚═════╝  ╚═════╝ ╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝


BGX RIPPER

 __________________________________________
|                                          |
|         Designed By Joseph Craig         |
|__________________________________________|

    """)


async def gather_bgx_data(device_address, service_uuid, characteristic_uuid, connection_timeout, retry_delay, scan_timeout, verbose):
    """
    Gather data from a BGX BLE device.

    Args:
        device_address (str): The MAC address of the BLE device.
        service_uuid (str): The service UUID to connect to.
        characteristic_uuid (str): The characteristic UUID to read data from.
        connection_timeout (float): Timeout for the BLE connection.
        retry_delay (float): Delay between retries.
        scan_timeout (float): Timeout for BLE scanning.
        verbose (bool): Enable verbose output.
    """
    retries = 3
    device = None
    for attempt in range(retries):
        if verbose:
            print(f"Attempting to find device: {device_address}, attempt {attempt + 1}/{retries}")
            animate_progress_bar(int(scan_timeout))
        device = await BleakScanner.find_device_by_address(device_address, timeout=scan_timeout)
        if device:
            break
        print(f"Attempt {attempt + 1} of {retries}: Device not found. Retrying...")
        await asyncio.sleep(retry_delay)

    if not device:
        print("Device not found after multiple attempts. Please ensure the device is powered on and in range.")
        return

    try:
        async with BleakClient(device, timeout=connection_timeout) as client:
            is_connected = await client.is_connected()
            if verbose:
                print(f"Connected to device: {is_connected}")

            services = await client.get_services()
            relevant_services = [
                service for service in services
                if service.uuid == service_uuid or "xpress" in service.description.lower() or "gechoos" in service.description.lower()
            ]
            for service in relevant_services:
                print(f"Found Service: {service.uuid} - {service.description}")
                for characteristic in service.characteristics:
                    if "read" in characteristic.properties:
                        try:
                            await asyncio.sleep(1)
                            value = await client.read_gatt_char(characteristic.uuid)
                            print(f"Characteristic {characteristic.uuid}: {value}")
                            if characteristic.uuid == characteristic_uuid:
                                onboard_storage = await client.read_gatt_char(characteristic.uuid)
                                print(f"Onboard Storage Data: {onboard_storage}")
                        except asyncio.TimeoutError:
                            print(f"Read operation timed out for characteristic {characteristic.uuid}")
                        except BleakError as e:
                            print(f"Failed to read characteristic {characteristic.uuid}: {e}")
    except BleakError as e:
        print(f"An error occurred during connection or data gathering: {e}")


def animate_progress_bar(duration):
    """
    Display a progress bar animation for a given duration.

    Args:
        duration (int): Duration for the progress bar.
    """
    bar_length = 40
    try:
        for i in range(int(duration)):
            filled_length = int(bar_length * (i + 1) / duration)
            bar = "\033[92m#\033[0m" * filled_length + "-" * (bar_length - filled_length)
            sys.stdout.write(f"\rScanning: [{bar}] {int((i + 1) / duration * 100)}%")
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\n")
    except KeyboardInterrupt:
        sys.stdout.write("\nScanning interrupted by user.\n")
        sys.exit(0)


def signal_handler(sig, frame):
    """Handle SIGINT signal (Ctrl+C) to gracefully exit the program."""
    print("\nOperation interrupted by user. Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    from argparse import RawTextHelpFormatter

    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        description="""

██████╗  ██████╗ ██╗  ██╗    ██████╗ ██╗██████╗ ██████╗ ███████╗██████╗ 
██╔══██╗██╔════╝ ╚██╗██╔╝    ██╔══██╗██║██╔══██╗██╔══██╗██╔════╝██╔══██╗
██████╔╝██║  ███╗ ╚███╔╝     ██████╔╝██║██████╔╝██████╔╝█████╗  ██████╔╝
██╔══██╗██║   ██║ ██╔██╗     ██╔══██╗██║██╔═══╝ ██╔═══╝ ██╔══╝  ██╔══██╗
██████╔╝╚██████╔╝██╔╝ ██╗    ██║  ██║██║██║     ██║     ███████╗██║  ██║
╚═════╝  ╚═════╝ ╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝


BGX RIPPER

 __________________________________________
|                                          |
|         Designed By Joseph Craig         |
|__________________________________________|

        """,
        epilog="""
Configuration file format:
------------------------------------------
device_address=<MAC_ADDRESS>
service_uuid=<SERVICE_UUID>
characteristic_uuid=<CHARACTERISTIC_UUID>

Example:
device_address=XX:XX:XX:XX:XX:XX
service_uuid=F000C0E0-0451-4000-B000-000000000000
characteristic_uuid=F000C0E1-0451-4000-B000-000000000000
------------------------------------------

        """,
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "-f", "--config_file", required=True,
        help="Path to the configuration file containing device information."
    )
    parser.add_argument(
        "-ct", "--connection_timeout", type=float, default=10.0,
        help="Timeout value for the BLE connection in seconds."
    )
    parser.add_argument(
        "-rt", "--retry_delay", type=float, default=2.0,
        help="Delay between retries in seconds, adjustable to prevent overwhelming the BLE device."
    )
    parser.add_argument(
        "-st", "--scan_timeout", type=float, default=20.0,
        help="Timeout value for BLE scanning in seconds."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose output for debugging and detailed information."
    )
    args = parser.parse_args()

    print_intro()

    # Read configuration from the provided file
    try:
        with open(args.config_file, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
            for line in lines:
                if "=" not in line or len(line.split("=")) != 2:
                    raise ValueError("Each line in the configuration file must be in the format key=value.")
            if len(lines) < 3:
                raise ValueError("Configuration file is missing required fields.")
            device_address = lines[0].split("=")[1].strip().strip('"')
            service_uuid = lines[1].split("=")[1].strip().strip('"')
            characteristic_uuid = lines[2].split("=")[1].strip().strip('"')
            if not device_address or not service_uuid or not characteristic_uuid:
                raise ValueError("Device address, service UUID, or characteristic UUID is missing or improperly formatted in the configuration file.")
    except FileNotFoundError:
        print(f"Configuration file '{args.config_file}' not found.")
        sys.exit(1)
    except ValueError as ve:
        print(f"Configuration error: {ve}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to read configuration file: {e}")
        sys.exit(1)

    asyncio.run(
        gather_bgx_data(
            device_address, service_uuid, characteristic_uuid,
            args.connection_timeout, args.retry_delay, args.scan_timeout,
            args.verbose
        )
    )
