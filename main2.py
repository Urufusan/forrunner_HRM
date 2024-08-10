import asyncio
from pprint import pprint
import bitstruct
import struct
from bleak import BleakClient
import sys
global last_print
global last_beat
last_print = ""
last_beat = False
HR_MEAS = "00002A37-0000-1000-8000-00805F9B34FB"

async def run(address):
    last_line_len = 0
    async with BleakClient(address) as client:
        connected = client.is_connected
        # print("Connected: {0}".format(connected))
        
        def hr_val_handler(sender, data):
            global last_print
            global last_beat
            """Simple notification handler for Heart Rate Measurement."""
            (unused, rr_int, nrg_expnd, snsr_cntct_spprtd, snsr_detect, hr_fmt) \
                = bitstruct.unpack("b3b1b1b1b1b1", data)
            if hr_fmt:
                hr_val, = struct.unpack_from("<H", data, 1)  # uint16
            else:
                hr_val, = struct.unpack_from("<B", data, 1)  # uint8
            # print(repr(hr_fmt), repr(snsr_detect), repr(snsr_cntct_spprtd), repr(hr_val))
            # print(type(hr_val), repr(hr_val))
            # print("HR: {0:3} bpm. Complete raw data: {1} ".format(hr_val, data.hex(sep=':')), end="\r")
            last_beat = not last_beat
            final_print = f"|HR: {(hr_val if snsr_detect else ' --'):3} BPM {'♥︎' if last_beat else ' '}|"
            #if last_print != final_print:
            print(final_print)# end="\r")
            print(final_print, file=sys.stderr)
            last_print = final_print
            # sys.stdout.flush()
        # pprint([serv_o.description for serv_o in client.services.services.values()])
        await client.start_notify(HR_MEAS, hr_val_handler)

        while client.is_connected:
            await asyncio.sleep(1)


if __name__ == "__main__":
    address = ("38:F9:F5:40:81:D1".lower())  # Change to address of device
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(address))
