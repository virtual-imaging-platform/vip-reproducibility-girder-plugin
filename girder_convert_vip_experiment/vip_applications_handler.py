"""
This module provides a route to get the list of applications as a json.
"""
import json
from girder.api import access
from girder.api.rest import Resource
from girder.api.describe import Description, autoDescribeRoute
from girder.models.setting import Setting

from .conversion_plugin_settings import ConversionPluginSettings


class VipApplicationsHandler(Resource):
    """Class used to provide a route to get the list of applications as a json."""
    DEFAULT_USER = 'ANONYMOUS'

    def __init__(self):
        super().__init__()
        self.resourceName = 'vip_applications'
        self.settings = Setting()
        self.resourceName = 'vip_applications'
        self.route('GET', (), self.get_applications)

    @access.public
    @autoDescribeRoute(
         Description("Get the list of applications as a json")
            .errorResponse('ID was invalid')
    )
    def get_applications(self):
        """Get the list of applications as a json"""
        file_path = Setting().get(ConversionPluginSettings.SETTING_KEY).get('applications_file_path')
        with open(file_path + "/applications.json", "r", encoding='utf-8') as json_file:
            json_file = json.load(json_file)
        return json_file
