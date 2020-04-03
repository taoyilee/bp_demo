# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import asyncio

from bleak import BleakClient

from uci_cbp_demo.bluetooth.unpack_drgcbp import unpack_cap


class RealDataSource_v2:
    CHARAC_UUID = "71ee1401-1232-11ea-8d71-362b9e155667"
    last_time = 0
    current_time = 0
    delta_time = 0
    MAC_ADDR = "CA:E7:1B:E8:10:B3"
    UUID_ADDR = None
    use_mac = True

    def callback(self, _, data):
        new_data = unpack_cap(data)
        new_delta_time = new_data["time"] - self.last_time
        self.delta_time = new_delta_time if new_delta_time > 0 else self.delta_time
        self.current_time += self.delta_time
        self.last_time = new_data["time"]
        self.queue.put({"time": self.current_time, "cap": new_data["cap"]})

    async def notify(self, client, loop):
        print(f"Connecting to {client.address}...")
        await client.connect()
        print(f"Starting notify...")
        await client.start_notify(self.CHARAC_UUID, self.callback)
        print(f"Starting notify done...")

    async def clean_up(self, client, loop):
        print(f"Stopping notification...")
        await client.stop_notify(self.CHARAC_UUID)
        print(f"Disconnecting...")
        await client.disconnect()

    def __call__(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        if self.use_mac:
            client = BleakClient(self.MAC_ADDR, loop=loop)
        else:
            client = BleakClient(self.UUID_ADDR, loop=loop)

        try:
            loop.create_task(self.notify(client, loop))
            loop.run_forever()
        except KeyboardInterrupt:
            print("Stopping...")
            loop.run_until_complete(self.clean_up(client, loop))
            loop.stop()
        finally:
            loop.close()

    def __init__(self, q, mac: str = None, uuid: str = None):
        if mac is not None and uuid is not None:
            raise ValueError("Only one of MAC and UUID can be specified.")
        if mac is not None:
            self.use_mac = True
            self.MAC_ADDR = mac.strip()
        if uuid is not None:
            self.use_mac = False
            self.UUID_ADDR = uuid.strip()
        self.queue = q


class MockDataSource:
    last_time = 0
    current_time = 0
    delta_time = 0

    def get_data(self):
        return next(self._data_source)

    def __init__(self, queue):
        from uci_cbp_demo.mock_sensor_data import cap
        self._data_source = cap()
        self.queue = queue

    @asyncio.coroutine
    def generate_data(self):
        while True:
            new_data = unpack_cap(self.get_data())
            new_delta_time = new_data["time"] - self.last_time
            self.delta_time = new_delta_time if new_delta_time > 0 else self.delta_time
            self.current_time += self.delta_time
            self.last_time = new_data["time"]
            self.queue.put({"time": self.current_time, "cap": new_data["cap"]})
            yield from asyncio.sleep(0.02)

    def __call__(self, *args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.create_task(self.generate_data())
        loop.run_until_complete(task)
