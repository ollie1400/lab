from picoscope import ps3000a
import argparse
import time
from enum import Enum
import plotly.graph_objects as go
from typing import Dict
import numpy

def discover_devices(print_devices=True):
    """
    Returns a list of serial numbers of discovered devices
    """
    ps = ps3000a.PS3000a(connect=False)
    serial_numbers = ps.enumerateUnits()

    if print_devices:
        print("Found PS3000 devices:")
        for s in serial_numbers:
            print(f"- {s}")
    
    return serial_numbers


class Channel(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"

class Coupling(Enum):
    AC = "AC"
    DC = "DC"

class ChannelSetup:
    def __init__(self) -> None:
        self.coupling = Coupling.DC
        self.voltage_range_V:float = 0.05
        self.voltage_offset_V:float = 0.0


def flash_led(serial_number:str, num_flashes=5):
    ps = ps3000a.PS3000a(serialNumber=serial_number, connect=True)
    ps.flashLed(times=num_flashes)
    time.sleep(num_flashes/2)


def record_trace(serial_number:str,
                 channel_setup:Dict[Channel, ChannelSetup]=None,
                 num_captures=1,
                 sample_rate_Hz=1000,
                 recording_duration_s=1):
    ps = ps3000a.PS3000a(serialNumber=serial_number, connect=True)
    ps.setChannel(channel="A", coupling="DC", VRange=10)

    sample_interval = 1.0 / sample_rate_Hz
    actual_sample_interval, actual_num_samples, max_samples =  ps.setSamplingInterval(sample_interval, recording_duration_s)
    ps.setSimpleTrigger("A", threshold_V=0.2, enabled=True)

    samples_per_segment = ps.memorySegments(num_captures)
    ps.setNoOfCaptures(num_captures)

    data = numpy.zeros((num_captures, actual_num_samples), dtype=numpy.int16)

    t1 = time.time()

    ps.runBlock()
    ps.waitReady()

    t2 = time.time()
    print("Time to get sweep: " + str(t2 - t1))

    ps.getDataRawBulk(data=data)

    numpy.mean(data)

    # plot data
    fig = go.Figure(layout=dict(
        title=f"Data",
        xaxis_title="Date / time"
    ))

    times = numpy.arange(data.shape[1])
    voltages_V = data[0,:]

    # times are stored as timestamps, convert to datetime for plotting
   # times = [datetime.datetime.fromtimestamp(t) for t in times]

    fig.add_trace(go.Scatter(
        x=times,
        y=voltages_V,
        name="Voltage"
    ))
    html_file = "data" + ".html"
    fig.write_html(html_file, auto_open=True)
    print(html_file)

if __name__ == "__main__":
    DEFAULT_SERIAL_NUMBER="JP507/0034"
    parser = argparse.ArgumentParser(description="""
    Utilities to gather data from the PicoScope
    """)
    parser.add_argument("--serial_number", "-n",
                        dest="serial_number",
                        default=DEFAULT_SERIAL_NUMBER,
                        help="The serial number of the PicoScope to connect to")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--flash_led", "-f",
                       dest="flash_led",
                       action="store_true",
                       help="Flash the LED")
    group.add_argument("--list_devices", "-l",
                       dest="list_devices",
                       action="store_true",
                       help="Print out serial numbers of all connected devices")
    group.add_argument("--record_trace", "-r",
                       dest="record_trace",
                       metavar=("DATA_FILE"),
                       nargs=1,
                       help="""
                       Plot the data in file [DATA_FILE] that was generated with the --record_iv option""")
    
    args = parser.parse_args()
    if args.flash_led:
        flash_led(args.serial_number)
    elif args.list_devices:
        discover_devices(print_devices=True)
    elif args.record_trace is not None:
        record_trace(
            serial_number=args.serial_number
        )
    else:
        parser.print_help()