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
        'timestamp': index,
        'value': values,
        'quality_flag': quality}
    return pd.DataFrame(index=index, data=data)


def static_forecast_values():
    index, values, quality = generate_randoms()
    data = {
        'timestamp': index,
        'value': values}
    return pd.DataFrame(index=index, data=data)
