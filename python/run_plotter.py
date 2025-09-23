import os
import sys
# Ensure local python/ directory is on sys.path so imports like `osap` work
sys.path.insert(0, os.path.dirname(__file__))

import cv2
import asyncio
import traceback
import numpy as np
from osap.osap import OSAP
from osap.bootstrap.auto_usb_serial.auto_usb_serial import AutoUSBPorts
from maxl.types import MAXLInterpolationIntervals 
from modules.vvelocity_motion import VVelocityMachineMotion
from svg import svg_tools

system_interpolation_interval = MAXLInterpolationIntervals.INTERVAL_16384
system_twin_to_real_ms = 200

# rates are: 
    # 100  - clean
    # 500  - speed
    # 1500 - ludicrous

class PlotterController:
    def __init__(
            self, 
            draw_rate: int = 100, 
            jog_rate: int = 100, 
            machine_extents = [235, 305]
        ):
        self.osap = None
        self.machine = None
        self.loop_task = None
        self.started = False
        self.draw_rate = draw_rate
        self.jog_rate = jog_rate
        self.machine_extents = machine_extents

    async def start(self):
        if self.started:
            return
        try:
            self.osap = OSAP("py-printer")
            loop = asyncio.get_event_loop()
            self.loop_task = loop.create_task(self.osap.runtime.run())
            usbserial_links = AutoUSBPorts().ports
            for usbserial in usbserial_links:
                self.osap.link(usbserial)
            await asyncio.sleep(0.25)
            system_map = await self.osap.netrunner.update_map()
            system_map.print()
            await self.osap.netrunner.await_time_settle(print_updates=True)
            self.machine = VVelocityMachineMotion(self.osap, system_interpolation_interval, system_twin_to_real_ms, extents = self.machine_extents)
            await self.machine.begin()
            await asyncio.sleep(1)
            await self.machine.queue_planner.goto_via_queue([0,0,0], self.draw_rate)
            self.started = True
        except Exception as err:
            print("ERROR during start:")
            print(err)
            print(traceback.format_exc())
            await self.shutdown()
            raise

    async def home(self):
        if not self.machine:
            raise RuntimeError("Machine not started")
        await self.machine.home()

    async def goto_origin(self):
        if not self.machine:
            raise RuntimeError("Machine not started")
        await self.machine.queue_planner.goto_via_queue([0,0,0], self.draw_rate)

    async def flush(self):
        if not self.machine:
            raise RuntimeError("Machine not started")
        await self.machine.queue_planner.flush_queue()

    async def shutdown(self):
        try:
            if self.machine is not None:
                await self.machine.queue_planner.goto_via_queue([0,0,0], self.draw_rate)
                await self.machine.queue_planner.flush_queue()
                await self.machine.shutdown()
        finally:
            self.machine = None
            self.started = False
            print("shutdown OK")

async def main():
    controller = PlotterController()
    try:
        await controller.start()
        ######################################################
        ############## DRAWING CODE STARTS HERE ##############
        ######################################################
        # Add drawing logic here or use controller methods from elsewhere
        ######################################################
        ############### DRAWING CODE ENDS HERE ###############
        ######################################################
        await asyncio.sleep(1)
        await controller.goto_origin()
        await controller.flush()
    except Exception as err:
        print("ERROR:")
        print(err)
        print(traceback.format_exc())
    finally:
        print("Finally: attempting shutdown...")
        await controller.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
