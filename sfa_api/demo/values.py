import os


import pandas as pd
import numpy as np

# Available variables in the demo_data directory
# as files with more realistic demo data are added
# they should be included here.
demo_file_variables = ['ghi', 'dni', 'dhi']


def demo_file_location(variable, freq):
    """Returns a path to possible demo data file.
    """
    directory = os.path.dirname(__file__)
    filename = f'{variable}_{freq}min.csv'
    file_path = os.path.join(directory, 'demo_data', filename)
    return file_path


def generate_randoms(freq):
    """Generates two days worth of random noisy data.

    Parameters
    ----------
    freq: int
        The "interval length" of the data to produce in minutes.
        options: 1 or 5

    Returns
    -------
    Dataframe
        Dataframe with datetimeindex, values and quality_flag
        columns.

    Notes
    -----
    Won't throw an error if you try to use a freq of other
    than 1 or 5 but will provide you values as though
    you selected 5.
    """
    if freq == 1:
        length = 4320
    else:
        # assume 5 minutes
        length = 864
    index = pd.date_range(start=pd.Timestamp('20190414T07:00'),
                          periods=length, freq=f'{freq}min', tz='UTC')
    values = np.random.normal(50, 5, size=length)
    quality_flags = np.random.randint(11, size=length)
    return index, values, quality_flags


def static_observation_values(variable=None, freq=5):
    if variable in demo_file_variables:
        filename = demo_file_location(variable, freq)
        obs_df = pd.read_csv(filename)
        obs_df = obs_df.set_index('timestamp')
        obs_df.index = pd.to_datetime(obs_df.index)
    else:
        index, values, quality = generate_randoms(freq=freq)
        data = {
            'value': values,
            'quality_flag': quality}
        obs_df = pd.DataFrame(index=index, data=data)
    obs_df.index.name = 'timestamp'
    return obs_df


def static_forecast_values(variable=None, freq=5):
    if variable in demo_file_variables:
        filename = demo_file_location(variable, freq)
        fx_df = pd.read_csv(filename)
        fx_df = fx_df.set_index('timestamp')
        fx_df = fx_df.drop(columns='quality_flag')
        fx_df.index = pd.to_datetime(fx_df.index)
    else:
        index, values, quality = generate_randoms(freq=freq)
        data = {
            'value': values}
        fx_df = pd.DataFrame(index=index, data=data)
    fx_df.index.name = 'timestamp'
    return fx_df
