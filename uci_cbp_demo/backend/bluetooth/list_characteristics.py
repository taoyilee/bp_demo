#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import asyncio
import logging

from bleak.backends.service import BleakGATTService, BleakGATTCharacteristic, BleakGATTDescriptor

logger = logging.getLogger("bp_demo")


class DescriptorDesc:
    def __init__(self, bleak_descriptor: "BleakGATTDescriptor"):
        self.uuid = bleak_descriptor.uuid
        self.handle = bleak_descriptor.handle

    def __repr__(self):
        _s = f"Descriptor: {self.uuid} ({self.handle})\n"
        return _s


class CharacterDesc:
    def __init__(self, bleak_char: "BleakGATTCharacteristic"):
        self.uuid = bleak_char.uuid
        self.description = bleak_char.description
        self.properties = bleak_char.properties
        self.descriptors = []
        for d in bleak_char.descriptors:
            self.descriptors.append(DescriptorDesc(d))
        self.descriptors.sort(key=lambda x: x.uuid)

    def __repr__(self):
        _s = f"Characteristic: {self.uuid} ({self.description}); {','.join(self.properties)}\n"
        for d in self.descriptors:
            _s += f"\t\t{d}\n"

        return _s


class ServicesDesc:
    def __init__(self, bleak_service: "BleakGATTService"):
        self.uuid = bleak_service.uuid
        self.description = bleak_service.description
        self.char = []
        for c in bleak_service.characteristics:
            self.char.append(CharacterDesc(c))
        self.char.sort(key=lambda x: x.uuid)

    @property
    def characteristics(self):
        return self.char

    def __repr__(self):
        _s = f"Service: {self.uuid} ({self.description})\n"
        for c in self.char:
            _s += f"\t{c}\n"
        import re
        _s = re.sub('\n+', '\n', _s)
        _s = re.sub('\n$', '', _s)
        return _s


def list_char(addr):
    from bleak import BleakClient
    services = []

    async def run(address, loop):
        async with BleakClient(address, loop=loop) as client:
            await client.is_connected()
            services.extend([ServicesDesc(s) for s in client.services])

    loop = asyncio.get_event_loop()
    logger.info(f"Connecting to {addr}")
    loop.run_until_complete(run(addr, loop))
    return services
