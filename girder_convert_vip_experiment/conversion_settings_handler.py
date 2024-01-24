"""
This file contains the ConversionSettingsHandler class, which provides a route to get the plugin 
api conf.
"""
import girder.models.setting as Setting
from girder.api import access
from girder.api.rest import Resource
from girder.api.describe import Description, autoDescribeRoute

from .conversion_plugin_settings import ConversionPluginSettings


class ConversionSettingsHandler(Resource):
    """Class used to provide a route to get the plugin api conf."""
    @access.user
    @autoDescribeRoute(
        Description('Get the plugin api conf')
    )
    def get_conversion_plugin_conf(self):
        """Get the plugin api conf."""
        return Setting().get(ConversionPluginSettings.SETTING_KEY)
    