"""
This module contains the settings for the conversion plugin.
"""
import jsonschema

from girder.exceptions import ValidationException
from girder.utility import setting_utilities


class ConversionPluginSettings(object):
    """Class used to define the settings of the conversion plugin."""
    SETTING_KEY = 'conversion_plugin.settings'


@setting_utilities.default(ConversionPluginSettings.SETTING_KEY)
def _defaultConversionSettings():
    return {
        'data_path': 'TO SET',
        'girder_id_outputs': 'TO SET',
        'target_name': 'experiment_id',
        'applications_file_path': 'TO SET'
    }


@setting_utilities.validator(ConversionPluginSettings.SETTING_KEY)
def _validateConversionSettings(doc):
    conversion_settings_schema = {
        'type': 'object',
        'properties': {
            'data_path': {
                'type': 'string'
            },
            'girder_id_outputs': {
                'type': 'string'
            },
            'target_name': {
                'type': 'string'
            }
        },
        'required': ['data_path', 'girder_id_outputs', 'target_name']
    }
    try:
        jsonschema.validate(doc['value'], conversion_settings_schema)
    except jsonschema.ValidationError as e:
        raise ValidationException('Invalid conversion plugin settings: ' + str(e)) from e
