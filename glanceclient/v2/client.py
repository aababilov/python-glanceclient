# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import warlock

from glanceclient.openstack.common.apiclient import client
from glanceclient.v2 import images
from glanceclient.v2 import schemas


class ImageClient(client.BaseClient):
    """Client for the OpenStack Images v2 API.

    """

    def __init__(self, *args, **kwargs):
        super(ImageClient, self).__init__(*args, **kwargs)
        self.schemas = schemas.Controller(self)
        self.images = images.Controller(self,
                                        self._get_image_model())

    def _get_image_model(self):
        schema = self.schemas.get('image')
        return warlock.model_factory(schema.raw())
