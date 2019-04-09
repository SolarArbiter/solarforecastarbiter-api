variable_mapping = {
    'ghi': ('GHI', '(W/m^2)'),
    'dni': ('DNI', '(W/m^2)'),
    'dhi': ('DHI', '(W/m^2)'),
    'temp_air': ('Air Temperature', '(&deg;C)'),
    'wind_speed': ('Wind Speed', '(m/s)'),
    'poa_global': ('Plane of Array Irradiance', '(W/m^2)'),
    'ac_power': ('AC Power', '(MW)'),
    'dc_power': ('DC Power', '(MW)'),
}


def api_to_dash_varname(api_varname):
    return variable_mapping[api_varname][0]


def api_varname_to_units(api_varname):
    return variable_mapping[api_varname][1]


def register_jinja_filters(app):
    app.jinja_env.filters['convert_varname'] = api_to_dash_varname
    app.jinja_env.filters['var_to_units'] = api_varname_to_units
