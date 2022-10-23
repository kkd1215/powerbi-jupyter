#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Embeds Power BI Report
"""

from ipywidgets import DOMWidget
from traitlets import Bool, Dict, HasTraits, Unicode, TraitError, validate, observe

from ._version import __version__
from .models import TokenType, ReportCreationMode
from .utils import MODULE_NAME, is_dataset_create_config_valid, get_access_token_details

QUICK_CREATE_EMBED_URL = "https://app.powerbi.com/quickCreate"

class QuickVisualize(DOMWidget, HasTraits):
    """Basic widget"""

    # Name of the widget view class in front-end
    _view_name = Unicode('QuickVisualizeView').tag(sync=True)

    # Name of the widget model class in front-end
    _model_name = Unicode('QuickVisualizeModel').tag(sync=True)

    # Name of the front-end module containing widget view
    _view_module = Unicode(MODULE_NAME).tag(sync=True)

    # Name of the front-end module containing widget model
    _model_module = Unicode(MODULE_NAME).tag(sync=True)

    # Version of the front-end module containing widget view
    _view_module_version = Unicode(__version__).tag(sync=True)

    # Version of the front-end module containing widget model
    _model_module_version = Unicode(__version__).tag(sync=True)

    # Default values for widget traits
    EMBED_CONFIG_DEFAULT_STATE = {
        'type': 'quickCreate',
        'accessToken': None,
        'embedUrl': QUICK_CREATE_EMBED_URL,
        'tokenType': TokenType.AAD.value,
        'tokenExpiration': None,
        'datasetCreateConfig': None,
        'reportCreationMode': ReportCreationMode.QUICK_EXPLORE.value
    }
    TOKEN_EXPIRED_DEFAULT_STATE = False
    INIT_ERROR_DEFAULT_STATE = ''

    # Authentication object
    _auth = None

    # Widget specific properties.
    # Widget properties are defined as traitlets. Any property tagged with `sync=True`
    # is automatically synced to the frontend *any* time it changes in Python.
    # It is synced back to Python from the frontend *any* time the model is touched in frontend.

    _embed_config = Dict(EMBED_CONFIG_DEFAULT_STATE).tag(sync=True)
    _embedded = Bool(False).tag(sync=True)
    _token_expired = Bool(TOKEN_EXPIRED_DEFAULT_STATE).tag(sync=True)
    _init_error = Unicode(INIT_ERROR_DEFAULT_STATE).tag(sync=True)

    # Authentication object
    _auth = None

    @validate('_embed_config')
    def _valid_embed_config(self, proposal):
        if proposal['value'] == self.EMBED_CONFIG_DEFAULT_STATE:
                return proposal['value']

        if (type(proposal['value']['type']) is not str):
            raise TraitError('Invalid type ', proposal['value']['type'])
        if ((type(proposal['value']['accessToken']) is not str) or (proposal['value']['accessToken'] == '')):
            raise TraitError('Invalid accessToken ', proposal['value']['accessToken'])
        if (type(proposal['value']['embedUrl']) is not str):
            raise TraitError('Invalid embedUrl ', proposal['value']['embedUrl'])
        if (type(proposal['value']['tokenType']) is not int):
            raise TraitError('Invalid tokenType ', proposal['value']['tokenType'])
        if (type(proposal['value']['tokenExpiration']) is not int):
            raise TraitError('Invalid tokenExpiration ', proposal['value']['tokenExpiration'])
        if (not is_dataset_create_config_valid(proposal['value']['datasetCreateConfig'])):
            raise TraitError('Invalid datasetCreateConfig ', proposal['value']['datasetCreateConfig'])
        if (type(proposal['value']['reportCreationMode']) is not str):
            raise TraitError('Invalid reportCreationMode ', proposal['value']['reportCreationMode'])
        return proposal['value']

    # Raise exception for errors when embedding the Power BI quick visualization
    @observe('_init_error')
    def _on_error(self, change):
        raise Exception(change['new'])

    # Methods
    def __init__(self, dataset_create_config, auth=None, **kwargs):
        """Create an instance of Quick Visualization in Power BI

        Args:
            dataset_create_config (object): Required.
                # TODO: add description

            auth (string or object): Optional.
                We have 3 authentication options to embed a Power BI report:
                 - Access token (string)
                 - Authentication object (object) - instance of AuthenticationResult (DeviceCodeLoginAuthentication or InteractiveLoginAuthentication)
                 - If not provided, Power BI user will be authenticated using Device Flow authentication

        Returns:
            object: QuickVisualize object
        """

        access_token, token_expiration = get_access_token_details(powerbi_widget=QuickVisualize, auth=auth)
        self._update_embed_config(access_token=access_token, token_expiration=token_expiration, dataset_create_config=dataset_create_config)
        self.observe(self._update_access_token, '_token_expired')

        # Init parent class DOMWidget
        super(QuickVisualize, self).__init__(**kwargs)
    
    def _update_access_token(self, change):
        if change.new == True:
            if not self._auth:
                raise Exception("Authentication context not found")
            self._auth.refresh_token()
            self._update_embed_config(access_token=self._auth.get_access_token(), token_expiration=self._auth.get_access_token_details().get('id_token_claims').get('exp'))
            self._token_expired = bool(self.TOKEN_EXPIRED_DEFAULT_STATE)

    def set_access_token(self, access_token):
        """Set access token for Power BI quick visualization

        Args:
            access_token (string): report access token
        """
        if not access_token:
            raise Exception("Access token cannot be empty")
        self._update_embed_config(access_token=access_token)

    def _update_embed_config(self, access_token=None, token_expiration=None, dataset_create_config=None):
        if access_token is not None:
            self._embed_config['accessToken'] = access_token

        if token_expiration is not None:
            self._embed_config['tokenExpiration'] = token_expiration

        if dataset_create_config is not None:
            self._embed_config['datasetCreateConfig'] = dataset_create_config
        
        self._embedded = False