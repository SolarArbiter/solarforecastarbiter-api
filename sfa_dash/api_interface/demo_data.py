site = {
  "elevation": 595.0,
  "extra_parameters": {
    "net_work_api_abbreviation": "AS",
    "network": "Universit of Oregon SRML",
    "network_api_id": "94040"
  },
  "latitude": 42.19,
  "longitude": -122.7,
  "modeling_parameters": {
  },
  "name": "Ashland OR",
  "provider": "Reference",
  "site_id": "123e4567-e89b-12d3-a456-426655440001",
  "timezone": "Etc/GMT+8"
}
site_1 ={
   "elevation": 786.0,
   "extra_parameters": {
       "network": "NREL MIDC",
   },
   "latitude": 32.22969,
   "longitude": -110.95534,
   "modeling_parameters": {
       "ac_power": "",
       "axis_azimuth": 45.0,
       "axis_tilt": 45.0,
       "backtrack": True,
       "dc_power": "",
       "gamma_pdc": "",
       "ground_coverage_ratio": 0.5,
       "surface_azimuth": 45.0,
       "surface_tilt": 45.0,
       "tracking_type": ""
    },
    "name": "SOLRMAP University of Arizona (OASIS)",
    "provider": "Reference",
    "site_id": "d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a",
    "timezone": "America/Pheonix"
}
site_2 = {
    "elevation": 786.0,
    "extra_parameters": {
    },
    "latitude": 43.73403,
    "longitude": -96.62328,
    "modeling_parameters": {
        "ac_power": "0.015",
        "dc_power": "0.015",
        "backtrack": True,
        "temperature_coefficient": -.002,
        "ground_coverage_ratio": 0.5,
        "surface_azimuth": 180,
        "surface_tilt": 45.0,
        "tracking_type": "Fixed"
    },
    "name": "Power Plant 1",
    "provider": "Reference",
    "site_id": "8594d9a2-a23d-4f62-a410-5dddcba583a7",
    "timezone": "Etc/GMT+6"
}
observation = {
    "extra_parameters": {
      "instrument": "Ascension Technology Rotating Shadowband Pyranometer"
    },
    "name": "GHI Instrument 1",
    "obs_id": "123e4567-e89b-12d3-a456-426655440000",
    "provider": "UO SRML",
    "site": site,
    "site_id": "123e4567-e89b-12d3-a456-426655440001",
    "variable": "GHI",
    "value_type": "Interval Mean",
    "interval_label": "beginning"
}
observation_1 = {
    "extra_parameters": {
      "instrument": "Ascension Technology Rotating Shadowband Pyranometer"
    },
    "name": "DHI Instrument 1",
    "obs_id": "9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f",
    "provider": "UO SRML",
    "site": site,
    "site_id": "123e4567-e89b-12d3-a456-426655440001",
    "variable": "dhi",
    "value_type": "Interval Mean",
    "interval_label": "beginning"
}
observation_2 = {
    "extra_parameters": {
      "instrument": "Ascension Technology Rotating Shadowband Pyranometer"
    },
    "name": "DNI Instrument 2",
    "obs_id": "9ce9715c-bd91-47b7-989f-50bb558f1eb9",
    "provider": "UO SRML",
    "site": site,
    "site_id": "123e4567-e89b-12d3-a456-426655440001",
    "variable": "dni",
    "value_type": "Interval Mean",
    "interval_label": "beginning"
}
observation_3 = {
    "extra_parameters": {
      "instrument": "Kipp & Zonen CMP 22 Pyranometer"
    },
    "name": "OASIS, ghi",
    "obs_id": "548a6c6e-a685-4690-87a8-ba7aab448bdb",
    "provider": "University of Arizona",
    "site": site_1,
    "site_id": "d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a",
    "variable": "ghi",
    "value_type": "Interval Mean",
    "interval_label": "beginning"
}
observation_4 = {
    "extra_parameters": {
      "instrument": "Kipp & Zonen CMP 22 Pyranometer"
    },
    "name": "Sioux Falls, ghi",
    "obs_id": "89d0ffa-936f-4d8e-8ad3-4241040e88d8",
    "provider": "NOAA",
    "site": site_2,
    "site_id": "8594d9a2-a23d-4f62-a410-5dddcba583a7",
    "variable": "ghi",
    "value_type": "Interval Mean",
    "interval_label": "beginning"
}

forecast = {
  "forecast_id": "f79e4f84-e2c3-11e8-9f32-f2801f1b9fd1",
  "name": "DA Power",
  "provider": "Provider A",
  "site": site_2,
  "site_id": "123e4567-e89b-12d3-a456-426655440001",
  "variable": "AC Power",
  "issue_time_of_day": "06:00",
  "issue_frequency": "1 day",
  "duration": "1 minute",
  "intervals": "1440",
  "interval_label": "beginning",
  "lead_time_to_start": "1 hour",
  "value_type": "mean",
}
observations = [ observation, observation_1, observation_2 ]
forecasts = [forecast]
sites = [site, site_1, site_2]
