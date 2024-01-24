"""
This module contains a Girder REST endpoint that allows admins to set a user's
canConvert flag (which determines whether or not they can convert experiments).
"""
from girder.api import access
from girder.api.rest import Resource, filtermodel
from girder.api.describe import Description, autoDescribeRoute
from girder.models.setting import Setting
from girder.models.user import User
from girder.constants import AccessType
from girder.exceptions import AccessException, RestException


class UserConvertHandler(Resource):
    """Class used to provide a route to set a user's canConvert flag."""
    DEFAULT_USER = 'ANONYMOUS'

    def __init__(self):
        super().__init__()
        self.resourceName = 'user_with_convert'
        self.settings = Setting()
        User().exposeFields(level=AccessType.READ, fields={'canConvert'})
        self._model = User()
        self.route('PUT', (':id',), self.update_user)

    @access.user
    @filtermodel(model=User)
    @autoDescribeRoute(
        Description("Update a user's information.")
        .modelParam('id', model=User, level=AccessType.WRITE)
        .param('can_convert', 'Can the user convert an experiment (admin access required)',
                required=False, dataType='boolean')
        .errorResponse()
        .errorResponse(('You do not have write access for this user.',
                        'Must be an admin to create an admin.'), 403)
    )
    def update_user(self, user, can_convert):
        """Update a user's information."""
        # Only admins can change canConvert state
        if not self.getCurrentUser()['admin']:
            raise AccessException('Only admins may change canConvert status.')
        if can_convert not in (True, False):
            raise RestException('canConvert must be a boolean.')

        user['canConvert'] = can_convert

        return self._model.save(user)
