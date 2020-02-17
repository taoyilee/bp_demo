# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import asyncio

from bleak import BleakClient

from uci_cbp_demo.unpack_drgcbp import unpack_characteristic_data, unpack_cap


class RealDataSource_v2:
    mac_addr = "CA:E7:1B:E8:10:B3"
    CHARAC_UUID = "71ee1401-1232-11ea-8d71-362b9e155667"
    last_time = 0
    current_time = 0
    delta_time = 0

    def callback(self, _, data):
        new_data = unpack_cap(data)
        new_delta_time = new_data["time"] - self.last_time
        self.delta_time = new_delta_time if new_delta_time > 0 else self.delta_time
        self.current_time += self.delta_time
        self.last_time = new_data["time"]
        self.queue.put({"time": self.current_time, "cap": new_data["cap"]})

    async def notify(self, client, loop):
        print(f"Connecting...")
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
        client = BleakClient(self.mac_addr, loop=loop)
        try:
            loop.create_task(self.notify(client, loop))
            loop.run_forever()
        except KeyboardInterrupt:
            print("Stopping...")
            loop.run_until_complete(self.clean_up(client, loop))
            loop.stop()
        finally:
            loop.close()

    def __init__(self, q):
        self.queue = q


class RealDataSource:
    mac_addr = "CA:E7:1B:E8:10:B3"
    CHARAC_UUID = "71ee1401-1232-11ea-8d71-362b9e155667"

    def callback(self, _, data):
        print("Callback...")
        new_data = unpack_characteristic_data(data)
        for i, time in enumerate(new_data["time"]):
            # print(f"{new_data['cap'][i]:.2f}pF @ ch: {new_data['channel'][i]}")
            # print({"time": time,
            #        "cap1": new_data["cap"][i] if new_data["channel"][i] == 0 else None,
            #        "cap2": new_data["cap"][i] if new_data["channel"][i] == 1 else None})
            self.queue.put({"time": time,
                            "cap1": new_data["cap"][i] if new_data["channel"][i] == 0 else None,
                            "cap2": new_data["cap"][i] if new_data["channel"][i] == 1 else None})

    async def notify(self, client, loop):
        print(f"Connecting...")
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
        import asyncio
        from bleak import BleakClient

        # loop = asyncio.get_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        client = BleakClient(self.mac_addr, loop=loop)

        try:
            loop.create_task(self.notify(client, loop))
            loop.run_forever()
        except KeyboardInterrupt:
            print("Stopping...")
            loop.run_until_complete(self.clean_up(client, loop))
            loop.stop()
        finally:
            loop.close()

    def __init__(self, q):
        self.queue = q


class MockDataSource:
    def _unpacking_generator(self):
        for d in self._data_source:
            new_data = unpack_characteristic_data(d)
            for i, time in enumerate(new_data["time"]):
                yield {"time": time,
                       "cap1": new_data["cap"][i] if new_data["channel"][i] == 0 else None,
                       "cap2": new_data["cap"][i] if new_data["channel"][i] == 1 else None}

    def get_data(self):
        return next(self._generator)

    def __init__(self, queue):
        from test.mock_sensor_data import sensor
        self._data_source = sensor()
        self._generator = self._unpacking_generator()
        self.queue = queue

    @asyncio.coroutine
    def generate_data(self):
        import random
        while True:
            n_new_data = random.randint(1, 5)
            for i in range(n_new_data):
                data = self.get_data()
                # print(data)
                self.queue.put(data)
            # print(f"#data: {n_new_data}")
            yield from asyncio.sleep(0.02)

    def __call__(self, *args, **kwargs):

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.create_task(self.generate_data())
        loop.run_until_complete(task)
