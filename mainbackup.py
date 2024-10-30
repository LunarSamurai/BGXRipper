import asyncio
from bleak import BleakClient, BleakScanner

# Replace this with the MAC address of your BGX device
BGX_DEVICE_ADDRESS = "XX:XX:XX:XX:XX:XX"
# Replace these with the specific UUIDs for the BGX BLE device
SERVICE_UUID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
CHARACTERISTIC_UUID = "xxxxxxxx-xxxx-xcxxx-xxxx-xxxxxxxxxxxx"

async def gather_bgx_data():
    device = await BleakScanner.find_device_by_address(BGX_DEVICE_ADDRESS, timeout=20.0)
    if not device:
        print("Device not found. Please ensure the device is powered on and in range.")
        return

    async with BleakClient(device) as client:
        try:
            is_connected = await client.is_connected()
            print(f"Connected: {is_connected}")

            # Read characteristic value (replace with actual UUIDs)
            data = await client.read_gatt_char(CHARACTERISTIC_UUID)
            print(f"Data from characteristic: {data}")

            # If there are multiple characteristics or services to read from, you can iterate over them
            services = await client.get_services()
            for service in services:
                print(f"Service: {service.uuid} - {service.description}")
                for characteristic in service.characteristics:
                    if "read" in characteristic.properties:
                        value = await client.read_gatt_char(characteristic.uuid)
                        print(f"Characteristic {characteristic.uuid}: {value}")

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(gather_bgx_data())
