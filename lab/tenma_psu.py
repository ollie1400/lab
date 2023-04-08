from plotly import graph_objects as go
import argparse
import time
import pandas
import signal
from lab.utilities import setup_logging
import logging
import datetime
import pickle

logger = logging.getLogger(__name__)

VERSION = "1.0.0"


def read_current_voltage_continuously(
        destination_pkl_file: str,
        measurement_period_s: float,
        measurement_duration: datetime.timedelta = None
) -> pandas.DataFrame:
    times = []
    voltages_V = []
    currents_A = []
    signal.signal(signal.SIGINT, signal.default_int_handler)
    data = None
    try:
        if measurement_duration is not None:
            measurement_end = datetime.datetime.now() + measurement_duration
        else:
            measurement_end = None
        while True:
            # read value
            voltage_V = 1.0
            current_A = 0.1
            time_s = time.time()

            logger.info(
                f"voltage_V={voltage_V:.6f},current_A={current_A:.6f}")

            times.append(time_s)
            voltages_V.append(voltage_V)
            currents_A.append(current_A)

            if measurement_end is not None and (datetime.datetime.now() > measurement_end):
                break

            if measurement_period_s > 0.0:
                time.sleep(measurement_period_s)
    finally:
        # save data to file
        values = pandas.DataFrame(data={
            "times": times,
            "voltages_V": voltages_V,
            "currents_A": currents_A
        })
        data = {
            "values": values,
            "file_name": destination_pkl_file,
            "version": VERSION
        }

        with open(destination_pkl_file, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f"Data written to file {destination_pkl_file}")
    return data


def plot_current_voltage_data_from_file(data_file: str):
    with open(data_file, 'rb') as f:
        data = pickle.load(f)

    plot_current_voltage_data(data)


def plot_current_voltage_data(data):
    file_name = data["file_name"]
    values = data["values"]
    fig = go.Figure(layout=dict(
        title=f"Current and Voltage<br>{file_name}",
        xaxis_title="Date / time"
    ))

    times = values["times"]
    voltages_V = values["voltages_V"]
    currents_A = values["currents_A"]

    # times are stored as timestamps, convert to datetime for plotting
    times = [datetime.datetime.fromtimestamp(t) for t in times]

    fig.add_trace(go.Scatter(
        x=times,
        y=voltages_V,
        name="Voltage"
    ))
    fig.add_trace(go.Scatter(
        x=times,
        y=currents_A,
        name="Current",
        yaxis="y2"
    ))
    fig.update_layout(
        yaxis1=dict(
            title="Voltage / V",
            side='left'
        ),
        yaxis2=dict(
            title="Current / A",
            side="right",
            overlaying='y'
        )
    )
    html_file = file_name + ".html"
    fig.write_html(html_file, auto_open=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    Utilities to log and plot information from the TENMA PSU
    """)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--record_iv", "-r",
                       dest="record_iv",
                       metavar=("DESTINATION_FILE", "PERIOD_S", "DURATION"),
                       nargs=3,
                       help="""
                       Record the current and voltage for a certain duration, save it, and plot it.
                       Data is written to a pandas DataFrame that is pickled to [DESTINATION_FILE].
                       A measurement is made every [PERIOD_S].
                       If [DURATION] is set to 0, then the measurement continue indefinitely.  If it is a number, it is interpreted to be a number of seconds.""")
    group.add_argument("--plot_iv", "-p",
                       dest="plot_iv",
                       metavar=("DATA_FILE"),
                       nargs=1,
                       help="""
                       Plot the data in file [DATA_FILE] that was generated with the --record_iv option""")

    args = parser.parse_args()
    setup_logging("tenma_psu.log", logger)

    if args.record_iv is not None:
        destination_file, period_s_str, duration_str = args.record_iv
        period_s = float(period_s_str)
        try:
            duration_s = float(duration_str)
            if duration_s == 0:
                measurement_duration = None
            else:
                measurement_duration = datetime.timedelta(seconds=duration_s)
        except:
            raise Exception(
                f"Unknown duration {duration_str}.  Must 0, or a float (number of seconds).")
        data = read_current_voltage_continuously(
            destination_file,
            measurement_period_s=period_s,
            measurement_duration=measurement_duration
        )
        plot_current_voltage_data(data)
    elif args.plot_iv is not None:
        data_file, = args.plot_iv
        plot_current_voltage_data_from_file(data_file)
    else:
        parser.print_help()
