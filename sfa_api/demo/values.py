import pandas as pd
import numpy as np


def generate_randoms():
    index = pd.date_range(start=pd.Timestamp('20190101T12:00'),
                          periods=20, freq='1 min', tz='UTC')
    values = np.random.uniform(20, 100, 20)
    quality_flags = np.random.randint(11, size=20)
    return index, values, quality_flags


def static_observation_values():
    index, values, quality = generate_randoms()
    data = {
        'value': values,
        'quality_flag': quality}
    obs_df = pd.DataFrame(index=index, data=data)
    obs_df.index.name = 'timestamp'
    return obs_df


def static_forecast_values():
    index, values, quality = generate_randoms()
    data = {
        'value': values}
    fx_df = pd.DataFrame(index=index, data=data)
    fx_df.index.name = 'timestamp'
    return fx_df
