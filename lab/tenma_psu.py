from plotly import graph_objects as go
import argparse
import time
import pandas
import signal
from lab.utilities import setup_logging
import logging
import datetime
import pickle


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

            logging.info(
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
        data = pandas.DataFrame(data={
            "times": times,
            "voltages_V": voltages_V,
            "currents_A": currents_A,
            "file_name": destination_pkl_file
        })

        with open(destination_pkl_file, 'wb') as f:
            pickle.dump(data, f)
    return data


def plot_current_voltage_data(data):
    file_name = data["file_name"]
    fig = go.Figure(layout=dict(
        title=f"{file_name}<br>Current and Voltage",
        xaxis_title="Date / time",
        yaxis1=dict(
            title="Voltage / V"
        ),
        yaxis2=dict(
            title="Current / A"
        )
    ))
    times = data["times"]
    voltages_V = data["voltages_V"]
    currents_A = data["currents_A"]
    fig.add_trace(
        x=times,
        y=voltages_V,
        name="Voltage"
    )
    fig.add_trace(
        x=times,
        y=currents_A,
        name="Current",
        yaxis="y2"
    )
    html_file = file_name + ".html"
    fig.write_html(html_file, autoopen=True)
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    Utilities to log and plot information from the TENMA PSU
    """)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--record_iv",
                       dest="record_iv",
                       metavar=("DESTINATION_FILE", "PERIOD_S", "DURATION"),
                       nargs=1,
                       help="""
                       Log the current and voltage for a certain duration.
                       Data is written to a pandas DataFrame that is pickled to [DESTINATION_FILE].
                       A measurement is made every [PERIOD_S].
                       If [DURATION] is set to 0, then the measurement continue indefinitely.  If it is a number, it is interpreted to be a number of seconds.""")

    args = parser.parse_args()
    setup_logging("tenma_psu.log", logging.getLogger(__name__))

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
