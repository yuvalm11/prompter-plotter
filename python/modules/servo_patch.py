from typing import cast
from osap.osap import OSAP
import asyncio


class ServoPatch:
    def __init__(self, osap: OSAP, device_name: str):
        self.device_name = device_name
        self._pen_up_rpc = osap.rpc_caller(device_name, "pen_up")
        self._pen_down_rpc = osap.rpc_caller(device_name, "pen_down")
        self.callers = [
            self._pen_up_rpc,
            self._pen_down_rpc
        ]
        
    async def begin(self):
        """Begin the ServoPatch module. set the pen to up position."""
        for caller in self.callers:
            await caller.begin()
        await asyncio.sleep(0.1)
        await self.pen_up()
    
    async def pen_up(self):
        """Raise the pen until limit switch is triggered.
        
        This function will rotate the servo at 80 degrees until the limit switch
        on D0 goes LOW (triggered), then stops the servo at 90 degrees (neutral).
        """
        await self._pen_up_rpc.call()
        return
    
    async def pen_down(self):
        """Lower the pen.
        
        This function rotates the servo at 95 degrees for 700ms,
        then stops at 90 degrees (neutral position).
        """
        await self._pen_down_rpc.call()
        return

