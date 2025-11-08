import os
import sys
import warnings
sys.path.insert(0, os.path.dirname(__file__))

import cv2
import asyncio
import traceback
import numpy as np
from osap.osap import OSAP
from osap.bootstrap.auto_usb_serial.auto_usb_serial import AutoUSBPorts
from maxl.types import MAXLInterpolationIntervals 
from modules.vvelocity_motion import VVelocityMachineMotion
from modules.servo_patch import ServoPatch
from svg import svg_tools

import requests
from utils import get_xys


system_interpolation_interval = MAXLInterpolationIntervals.INTERVAL_16384
system_twin_to_real_ms = 200

# rates are: 
    # 100  - clean
    # 500  - speed
    # 1500 - ludicrous

class PlotterController:
    def __init__(
            self, 
            draw_rate: int = 150, 
            jog_rate: int = 250,
            machine_extents = [235, 305]
        ):
        self.osap = None
        self.machine = None
        self.loop_task = None
        self.started = False
        self.draw_rate = draw_rate
        self.jog_rate = jog_rate
        self.machine_extents = machine_extents
        self.servo_patch = None
        self.pen_position = 0

    async def start(self):
        if self.started:
            return
        try:
            self.osap = OSAP("py-printer")
            loop = asyncio.get_event_loop()
            self.loop_task = loop.create_task(self.osap.runtime.run())
            self._usbserial_links = AutoUSBPorts().ports
            for usbserial in self._usbserial_links:
                self.osap.link(usbserial)
            await asyncio.sleep(0.25)
            system_map = await self.osap.netrunner.update_map()
            system_map.print()
            await self.osap.netrunner.await_time_settle(print_updates=True)
            self.machine = VVelocityMachineMotion(self.osap, system_interpolation_interval, system_twin_to_real_ms, extents = self.machine_extents)
            await self.machine.begin()

            self.servo_patch = ServoPatch(self.osap, "servo_patch")
            await self.servo_patch.begin()

            await asyncio.sleep(1)
            await self.goto([0,0,0], self.draw_rate)
            await self.flush()

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
        await self.goto_and_wait([0,0,0])
        

    async def flush(self):
        if not self.machine:
            raise RuntimeError("Machine not started")
        await self.machine.queue_planner.flush_queue()
    
    async def goto(self, position, rate=None):
        """Move to a position via the queue (non-blocking).
        
        Args:
            position: Target position as [x, y, z] or [x, y, z, e]
            rate: Movement rate. If None, uses self.draw_rate
        
        This queues the movement but returns immediately without waiting
        for completion. Use flush() or goto_and_wait() to ensure completion.
        """
        if not self.machine:
            raise RuntimeError("Machine not started")
        if rate is None:
            rate = self.draw_rate
        if position[2] != self.pen_position:
            warnings.warn("pen position can change only with goto_and_wait")
        await self.machine.queue_planner.goto_via_queue(position, rate)
    
    async def goto_and_wait(self, position, rate=None):
        """Move to a position and wait for completion.
        
        Args:
            position: Target position as [x, y, z] or [x, y, z, e]
            rate: Movement rate. If None, uses self.draw_rate
        
        This queues the movement and waits for it to complete before returning.
        """
        if not self.machine:
            raise RuntimeError("Machine not started")
        if rate is None:
            rate = self.draw_rate
        await self.machine.queue_planner.goto_and_await(position, rate)
        if position[2] != self.pen_position:
            self.pen_position = position[2]
            if self.pen_position == 0: await self.servo_patch.pen_up()
            else: await self.servo_patch.pen_down()
            await asyncio.sleep(1)

    async def shutdown(self):
        try:
            if self.machine is not None:
                await self.goto([0,0,0])
                await self.flush()
                await self.machine.shutdown()
        finally:
            # cancel runtime loop and dissolve links
            if self.loop_task is not None:
                self.loop_task.cancel()
                try:
                    await self.loop_task
                except BaseException:
                    pass
                self.loop_task = None
            # dissolve links from OSAP and close serials
            if self.osap is not None:
                for link in list(self.osap.runtime.links):
                    if link is not None:
                        try:
                            link.dissolve()
                        except Exception:
                            pass
            if hasattr(self, "_usbserial_links") and self._usbserial_links is not None:
                for usb in self._usbserial_links:
                    try:
                        if hasattr(usb, "close"):
                            usb.close()
                    except Exception:
                        pass
                self._usbserial_links = None
            self.machine = None
            self.started = False
            print("shutdown OK")

async def main():
    controller = PlotterController()
    try:
        await controller.start()
        # await controller.home()
        ######################################################
        ############## DRAWING CODE STARTS HERE ##############
        ######################################################
        # Add drawing logic here or use controller methods from elsewhere 
        pen = 0
        for _ in range(3):
            await controller.goto([-130,305,0], 1500)
            await controller.goto([0,0,0], 1500)
            await controller.goto([235,0,0], 1500)
            await controller.goto([365,305,0], 1500)
            pen = 1 - pen
        for _ in range(3):
            await controller.goto([0,0,0], 1500)
            await controller.goto([235,0,0], 1500)
            await controller.goto([-130,305,0], 1500)
            await controller.goto([365, 305, 0], 1500)
            pen = 1 - pen
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

async def test_servo_patch():
    """Test function for ServoPatch module."""
    print("=== ServoPatch Test ===")
    
    # Initialize OSAP
    osap = OSAP("servo-patch-test")
    loop = asyncio.get_event_loop()
    loop_task = loop.create_task(osap.runtime.run())
    
    try:
        # Connect to USB serial devices
        print("\nConnecting to USB devices...")
        usb_links = AutoUSBPorts().ports
        if not usb_links:
            print("ERROR: No USB devices found!")
            return
        
        for usb in usb_links:
            osap.link(usb)
            print(f"  - Linked to {usb.port}")
        

        await asyncio.sleep(0.25)
        system_map = await osap.netrunner.update_map()
        system_map.print()
        
        await osap.netrunner.await_time_settle(print_updates=True)
        
        servo_patch = ServoPatch(osap, "servo_patch")
        await servo_patch.begin()
        
        # Test pen_up
        print("\n--- Testing pen_up ---")
        await servo_patch.pen_up()
        print("  ✓ pen_up completed")
        await asyncio.sleep(1.2)
        
        # Test pen_down
        print("\n--- Testing pen_down ---")
        await servo_patch.pen_down()
        print("  ✓ pen_down completed")
        await asyncio.sleep(1.2)
        
        print("\n=== All tests completed successfully! ===")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as err:
        print(f"\n\nERROR during test:")
        print(f"  {err}")
        traceback.print_exc()
    finally:
        # Cleanup
        print("\nCleaning up...")
        if loop_task is not None:
            loop_task.cancel()
            try:
                await loop_task
            except:
                pass
        
        # Close USB serial connections
        if 'usb_links' in locals():
            for usb in usb_links:
                try:
                    if hasattr(usb, "close"):
                        usb.close()
                except:
                    pass
        
        if osap:
            for link in list(osap.runtime.links):
                if link is not None:
                    try:
                        link.dissolve()
                    except:
                        pass
        
        print("  ✓ Cleanup complete")

if __name__ == "__main__":
    asyncio.run(main())
