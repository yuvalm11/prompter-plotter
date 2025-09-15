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
draw_rate = 50
jog_rate = draw_rate
machine_extents = [250, 250]

async def main():
    try:
        machine = None 
        test_fet = None 
        osap = OSAP("py-printer")
        loop = asyncio.get_event_loop()
        loop.create_task(osap.runtime.run())
        usbserial_links = AutoUSBPorts().ports
        for usbserial in usbserial_links:
            osap.link(usbserial)
        await asyncio.sleep(0.25)
        system_map = await osap.netrunner.update_map()
        system_map.print()
        await osap.netrunner.await_time_settle(print_updates=True)
        machine = VVelocityMachineMotion(osap, system_interpolation_interval, system_twin_to_real_ms, extents = machine_extents)
        await machine.begin()
        await asyncio.sleep(1)

        # await machine.home()
        await machine.queue_planner.goto_via_queue([0,0,0], draw_rate)


        ######################################################
        ############## DRAWING CODE STARTS HERE ##############
        ######################################################


        

        ######################################################
        ############### DRAWING CODE ENDS HERE ###############
        ######################################################


        await asyncio.sleep(1)
        await machine.queue_planner.goto_via_queue([0,0,0], draw_rate)
        await machine.queue_planner.flush_queue()

    except Exception as err:
        print("ERROR:")
        print(err)
        print(traceback.format_exc())

    finally: 
        print("Finally: attempting shutdown...")
        if test_fet is not None:
            await test_fet.set_gate(0) 
        if machine is not None:
            await machine.shutdown() 
        print("shutdown OK")

if __name__ == "__main__":
    asyncio.run(main())
