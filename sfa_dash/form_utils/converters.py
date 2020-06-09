"""Contains converter objects for changing form submissions to api schema
compliant dictionaries for posting and vice versa.

Each converter subclasses the FormCoverter base class to enforce a common
interface. The converter's `form` attribute is the path of the form template
the converter is expected to parse.
"""
from abc import ABC, abstractmethod
from functools import reduce


from sfa_dash.form_utils import utils


class FormConverter(ABC):
    """Abstract base class to serve as an interface.
    """
    form = None

    @classmethod
    @abstractmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts an API schema compliant dictionary to a dict used for
        prefilling form fields.

        Parameters
        ----------
        payload_dict: dict
            API json schema object parsed into a dictionary.

        Returns
        -------
        dict
            Dictionary that mirrors the format of Flask's request.form. Keys
            should be the name of the HTML input element.
        """
        pass

    @classmethod
    @abstractmethod
    def formdata_to_payload(cls, form_dict):
        """Converts a dictionary of form submission data into a API schema
        compliant dictionary to a dict used for

        Parameters
        ----------
        form_dict: dict
            Dictionary of form submission data. Usually just Flask's
            request.form dict.

        Returns
        -------
        payload_dict: dict
            API json schema object parsed into a dictionary.
        """
        pass


class SiteConverter(FormConverter):
    form = 'forms/site_form.html'
    tracking_keys = {
        'fixed': ['surface_tilt', 'surface_azimuth'],
        'single_axis': ['axis_azimuth', 'backtrack', 'axis_tilt',
                        'ground_coverage_ratio', 'max_rotation_angle'],
    }
    modeling_keys = ['ac_capacity', 'dc_capacity', 'ac_loss_factor',
                     'dc_loss_factor', 'temperature_coefficient',
                     'tracking_type']

    top_level_keys = ['name', 'elevation', 'latitude', 'longitude', 'timezone',
                      'extra_parameters']

    @classmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts an api response to a form data dictionary for filling a
        form.

        Parameters
        ----------
        payload_dict: dict
            API json response as a python dict

        Returns
        -------
        dict
            dictionary of form data.
        """
        form_dict = {key: payload_dict[key]
                     for key in cls.top_level_keys
                     if key != 'extra_parameters'}
        # test if any 'modeling_parameter' items are not None
        is_plant = reduce(lambda a, b: a or b,
                          [x is not None for x in
                           payload_dict['modeling_parameters'].values()])
        if is_plant:
            form_dict['site_type'] = 'power-plant'
            modeling_params = payload_dict['modeling_parameters']
            for key in cls.modeling_keys:
                form_dict[key] = modeling_params[key]
            for key in cls.tracking_keys[modeling_params['tracking_type']]:
                form_dict[key] = modeling_params[key]
        else:
            form_dict['site_type'] = 'weather-station'
        return form_dict

    @classmethod
    def formdata_to_payload(cls, form_dict):
        """Formats the result of a site webform into an API payload.

        Parameters
        ----------
        form_dict:  dict
            The posted form data parsed into a dict.
        Returns
        -------
        dictionary
            Form data formatted to the API spec.
        """
        site_metadata = {key: form_dict[key]
                         for key in cls.top_level_keys
                         if form_dict.get(key, "") != ""}
        if form_dict['site_type'] == 'power-plant':
            modeling_params = {key: form_dict[key]
                               for key in cls.modeling_keys
                               if form_dict.get(key, "") != ""}
            tracking_type = form_dict['tracking_type']
            tracking_fields = {key: form_dict[key]
                               for key in cls.tracking_keys[tracking_type]}
            modeling_params.update(tracking_fields)
            site_metadata['modeling_parameters'] = modeling_params
        return site_metadata


class ObservationConverter(FormConverter):
    form = 'forms/observation_form.html'

    # keys that can be directly read from the form or api response
    direct_keys = ['name', 'variable', 'interval_value_type',
                   'uncertainty', 'extra_parameters', 'interval_label',
                   'site_id']

    @classmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts an observation metadata dict into a form_data dict.

        Parameters
        ----------
        payload: dict
            API observation metadata json repsonse as a dict.

        Returns
        -------
        dict
            A dictionary for filling out form fields where keys are input name
            attributes.
        """
        form_dict = {key: payload_dict[key]
                     for key in cls.direct_keys
                     if key != 'extra_parameters'}
        form_dict.update(
            utils.parse_timedelta_from_api(
                payload_dict,
                'interval_length'
            )
        )
        return form_dict

    @classmethod
    def formdata_to_payload(cls, form_dict):
        """Formats the result of a observation webform into an API payload.

        Parameters
        ----------
        form_dict:  dict
            The posted form data parsed into a dict.
        Returns
        -------
        dictionary
            Form data formatted to the API spec.
        """
        obs_metadata = {}
        obs_metadata = {key: form_dict[key]
                        for key in cls.direct_keys
                        if form_dict.get(key, "") != ""}
        obs_metadata['interval_length'] = utils.parse_timedelta_from_form(
            form_dict,
            'interval_length')
        return obs_metadata


class ForecastConverter(FormConverter):
    form = 'forms/forecast_form.html'
    direct_keys = ['name', 'variable', 'interval_value_type',
                   'extra_parameters', 'interval_label']

    @classmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts an forecast metadata dict into a form_data dict.

        Parameters
        ----------
        payload: dict
            API forecast metadata json repsonse as a dict.

        Returns
        -------
        dict
            A dictionary for filling out form fields where keys are input name
            attributes.
        """
        form_dict = {key: payload_dict[key]
                     for key in cls.direct_keys
                     if key != 'extra_parameters'}
        form_dict.update(utils.get_location_id(payload_dict))
        form_dict.update(
            utils.parse_hhmm_field_from_api(payload_dict, 'issue_time_of_day')
        )
        form_dict.update(
            utils.parse_timedelta_from_api(payload_dict, 'lead_time_to_start')
        )
        form_dict.update(
            utils.parse_timedelta_from_api(payload_dict, 'run_length')
        )
        form_dict.update(
            utils.parse_timedelta_from_api(payload_dict, 'interval_length')
        )
        return form_dict

    @classmethod
    def formdata_to_payload(cls, form_dict):
        """Formats the result of a forecast webform into an API payload.

        Parameters
        ----------
        form_dict:  dict
            The posted form data parsed into a dict.
        Returns
        -------
        dictionary
            Form data formatted to the API spec.
        """
        fx_metadata = {}
        fx_metadata = {key: form_dict[key]
                       for key in cls.direct_keys
                       if form_dict.get(key, '') != ''}
        fx_metadata.update(utils.get_location_id(form_dict))
        fx_metadata['issue_time_of_day'] = utils.parse_hhmm_field_from_form(
            form_dict,
            'issue_time_of_day')
        fx_metadata['lead_time_to_start'] = utils.parse_timedelta_from_form(
            form_dict,
            'lead_time_to_start')
        fx_metadata['run_length'] = utils.parse_timedelta_from_form(
            form_dict,
            'run_length')
        fx_metadata['interval_length'] = utils.parse_timedelta_from_form(
            form_dict,
            'interval_length')
        return fx_metadata


class CDFForecastConverter(FormConverter):
    form = 'forms/cdf_forecast_group_form.html'

    @classmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts a CDF forecast metadata dict into a form_data dict.

        Parameters
        ----------
        payload: dict
            API CDFforecast metadata json repsonse as a dict.

        Returns
        -------
        dict
            A dictionary for filling out form fields where keys are input name
            attributes.
        """
        form_data = ForecastConverter.payload_to_formdata(payload_dict)
        constant_values = [str(cv['constant_value'])
                           for cv in payload_dict['constant_values']]
        form_data['constant_values'] = ','.join(constant_values)
        form_data['axis'] = payload_dict['axis']
        return form_data

    @classmethod
    def formdata_to_payload(cls, form_dict):
        """Formats the result of a cdf forecast webform into an API payload.

        Parameters
        ----------
        form_dict:  dict
            The posted form data parsed into a dict.

        Returns
        -------
        dictionary
            Form data formatted to the API spec.
        """
        fx_metadata = ForecastConverter.formdata_to_payload(form_dict)
        constant_values = [float(x)
                           for x in form_dict['constant_values'].split(',')]
        fx_metadata['constant_values'] = constant_values
        fx_metadata['axis'] = form_dict['axis']
        return fx_metadata


class AggregateConverter(FormConverter):
    form = 'forms/aggregate_form.html'
    direct_keys = ['name', 'description', 'interval_label', 'aggregate_type',
                   'variable', 'timezone', 'extra_parameters']

    @classmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts an aggregate metadata dict into a form_data dict.

        Parameters
        ----------
        payload: dict
            API forecast metadata json repsonse as a dict.

        Returns
        -------
        dict
            A dictionary for filling out form fields where keys are input name
            attributes.

        Notes
        -----
            This function fills the aggregate ceation form and does not copy
            its corresponding observation.
        """
        form_dict = {key: payload_dict[key]
                     for key in cls.direct_keys
                     if key != 'extra_parameters'}
        form_dict.update(utils.parse_timedelta_from_api(
            payload_dict, 'interval_length'))
        return form_dict

    @classmethod
    def formdata_to_payload(cls, form_dict):
        """Converts an aggregate form submission dict to an api post payload.

        Parameters
        ----------
        form_dict: dict
            The posted form data parsed into a dict.

        Returns
        -------
        dict
            Form data formatted to API spec.
        """
        formatted = {key: form_dict[key]
                     for key in cls.direct_keys
                     if form_dict.get(key, '') != ''}
        formatted['interval_length'] = utils.parse_timedelta_from_form(
            form_dict, 'interval_length')
        return formatted


class ReportConverter(FormConverter):
    @classmethod
    def payload_to_formdata(cls, payload_dict):
        pass

    @classmethod
    def formdata_to_payload(cls, form_dict):
        pass
