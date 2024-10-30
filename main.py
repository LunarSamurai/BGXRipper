import asyncio
import argparse
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
import time
import sys
import signal

async def gather_bgx_data(device_address, service_uuid, characteristic_uuid, connection_timeout, retry_delay, scan_timeout, verbose):
    """
    Gather data from a BGX220S BLE device.

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
            progress_task = asyncio.create_task(animate_progress_bar(scan_timeout))
        device = await BleakScanner.find_device_by_address(device_address, timeout=scan_timeout)
        progress_task.cancel()  # Stop the progress bar once the scan completes
        try:
            await progress_task  # Wait for progress task to finish gracefully if not yet cancelled
        except asyncio.CancelledError:
            pass  # Wait for progress task to finish gracefully if not yet cancelled  # Scanning duration for scanning
        device = await BleakScanner.find_device_by_address(device_address, timeout=scan_timeout)
        if device:
            break
        print(f"\033[91m\nAttempt {attempt + 1} of {retries}: Device not found. Retrying...\033[0m")
        await asyncio.sleep(retry_delay)  # Adding a small delay to avoid overwhelming the BLE device or network
    
    if not device:
        print("Device not found after multiple attempts. Please ensure the device is powered on and in range.")
        return

    try:
        async with BleakClient(device, timeout=connection_timeout) as client:
            is_connected = await client.is_connected()
            if verbose:
              print(f"\033[92mConnected to device: {is_connected}\033[0m")

            # Read characteristic value (attempting to use likely relevant services)
            services = await client.get_services()
            relevant_services = [service for service in services if "bgx" in service.description.lower() or "xpress" in service.description.lower() or "gechoos" in service.description.lower()]
            for service in relevant_services:
                print(f"Found Service: {service.uuid} - {service.description}")
                for characteristic in service.characteristics:
                    if "read" in characteristic.properties:
                        try:
                            await asyncio.sleep(1)  # Adding a delay between characteristic reads to avoid overwhelming the device
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

import random

async def animate_progress_bar(duration):
    """
    Display a progress bar animation that progresses smoothly until scanning is complete.

    Args:
        duration (int): Estimated duration for the progress bar.
    """
    """
    Display a progress bar animation that progresses smoothly.

    Args:
        duration (int): Estimated duration for the progress bar.
    """
    bar_length = 40
    start_time = time.time()
    try:
        while not asyncio.current_task().cancelled():
            elapsed_time = time.time() - start_time
            progress = min(elapsed_time / duration, 1.0)
            filled_length = int(bar_length * progress)
            bar = "[92m#[0m" * filled_length + "-" * (bar_length - filled_length)
            sys.stdout.write(f"\rScanning: [{bar}] {int(progress * 100)}%")
            sys.stdout.flush()
            if progress >= 1.0:
                break
            await asyncio.sleep(0.1)  # Small delay to update the bar smoothly
        sys.stdout.write("")
    except KeyboardInterrupt:
        sys.stdout.write("Scanning interrupted by user.")
        sys.exit(0)

def signal_handler(sig, frame):
    print("\nOperation interrupted by user. Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    from argparse import RawTextHelpFormatter

    # ASCII Art and Intro Section
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

    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Argument Parsing
    parser = argparse.ArgumentParser(
        description="""
        BGX220S Data Gathering Tool - Designed for communicating with BGX220S BLE devices.
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

Imported Plugin Issues:
------------------------------------------
If you are getting any issues with the bleaker plugin, please run 
    : pip3 install bleaker
        - update/install to the latest version of python 3
        - update your pip using command 
            - python3 -m pip install --upgrade pip
------------------------------------------
        """,
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument("-f", "--config_file", required=True, help="Path to the configuration file containing device information.")
    parser.add_argument("--connection_timeout", type=float, default=10.0, help="Timeout value for the BLE connection in seconds.")
    parser.add_argument("--retry_delay", type=float, default=2.0, help="Delay between retries in seconds.")
    parser.add_argument("--scan_timeout", type=float, default=20.0, help="Timeout value for BLE scanning in seconds.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output for debugging and detailed information.")
    args = parser.parse_args()

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
        exit(1)
    except ValueError as ve:
        print(f"Configuration error: {ve}")
        exit(1)
    except Exception as e:
        print(f"Failed to read configuration file: {e}")
        exit(1)

    # Run the asyncio function
    asyncio.run(gather_bgx_data(device_address, service_uuid, characteristic_uuid, args.connection_timeout, args.retry_delay, args.scan_timeout, args.verbose))
