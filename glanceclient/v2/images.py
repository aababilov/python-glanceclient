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

import urllib


from glanceclient.common import utils
from glanceclient.openstack.common.apiclient import base

DEFAULT_PAGE_SIZE = 20


class Controller(base.Manager):
    def __init__(self, api, model):
        super(Controller, self).__init__(api)
        self.model = model

    def list(self, **kwargs):
        """Retrieve a listing of Image objects

        :param page_size: Number of images to request in each paginated request
        :returns generator over list of Images
        """
        def paginate(url):
            resp, body = self.api.get(url)
            for image in body['images']:
                yield image
            try:
                next_url = body['next']
            except KeyError:
                return
            else:
                for image in paginate(next_url):
                    yield image

        filters = kwargs.get('filters', {})

        if not kwargs.get('page_size'):
            filters['limit'] = DEFAULT_PAGE_SIZE
        else:
            filters['limit'] = kwargs['page_size']

        for param, value in filters.iteritems():
            if isinstance(value, basestring):
                filters[param] = utils.ensure_str(value)

        url = '/v2/images?%s' % urllib.urlencode(filters)

        for image in paginate(url):
            #NOTE(bcwaldon): remove 'self' for now until we have an elegant
            # way to pass it into the model constructor without conflict
            image.pop('self', None)
            yield self.model(**image)

    def get(self, image_id):
        url = '/v2/images/%s' % image_id
        resp, body = self.api.get(url)
        #NOTE(bcwaldon): remove 'self' for now until we have an elegant
        # way to pass it into the model constructor without conflict
        body.pop('self', None)
        return self.model(**body)

    def data(self, image_id, do_checksum=True):
        """
        Retrieve data of an image.

        :param image_id:    ID of the image to download.
        :param do_checksum: Enable/disable checksum validation.
        """
        url = '/v2/images/%s/file' % image_id
        resp, body = self.api.get(url)
        checksum = resp.headers.get('content-md5')
        if do_checksum and checksum is not None:
            return utils.integrity_iter(body, checksum)
        else:
            return body

    def delete(self, image_id):
        """Delete an image."""
        self.api.delete('v2/images/%s' % image_id)

    def update(self, image_id, **kwargs):
        """
        Update attributes of an image.

        :param image_id: ID of the image to modify.
        :param **kwargs: Image attribute names and their new values.
        """
        image = self.get(image_id)
        for (key, value) in kwargs.items():
            setattr(image, key, value)

        url = '/v2/images/%s' % image_id
        hdrs = {'Content-Type': 'application/openstack-images-v2.0-json-patch'}
        self.api.patch(url,
                       headers=hdrs,
                       body=image.patch)

        #NOTE(bcwaldon): calling image.patch doesn't clear the changes, so
        # we need to fetch the image again to get a clean history. This is
        # an obvious optimization for warlock
        return self.get(image_id)
