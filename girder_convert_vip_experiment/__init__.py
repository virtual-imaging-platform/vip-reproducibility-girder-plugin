"""
Init file for the plugin. It is used to register the plugin to Girder.
"""

# -----------------------------------------------------------------------------
# Description : entry point of the plugin
# Author      : Hippolyte Blot. <hippolyte.blot@creatis.insa-lyon.fr>
# -----------------------------------------------------------------------------

from girder.plugin import GirderPlugin

# Local imports
from .conversion_handler import ConversionHandler
from .vip_applications_handler import VipApplicationsHandler
from .user_convert_handler import UserConvertHandler
from .conversion_settings_handler import ConversionSettingsHandler


class ConvertVIPExperiment(GirderPlugin):
    """Main class of the plugin. Used to register the plugin to Girder and to add routes."""
    DISPLAY_NAME = 'Convert VIP experiment'
    CLIENT_SOURCE_PATH = 'web_client'

    def load(self, info):
        info['apiRoot'].convert = ConversionHandler()
        info['apiRoot'].vip_applications = VipApplicationsHandler()
        info['apiRoot'].change_conversion_rights = UserConvertHandler()
        info['apiRoot'].system.route('GET', ('setting', 'conversion_plugin'),
                                     ConversionSettingsHandler.get_conversion_plugin_conf)

        base_template_filename = info['apiRoot'].templateFilename
        info['apiRoot'].updateHtmlVars({
            'baseTemplateFilename': base_template_filename
        })
