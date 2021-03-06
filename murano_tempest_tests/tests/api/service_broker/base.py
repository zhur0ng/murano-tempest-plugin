# Copyright (c) 2015 Mirantis, Inc.
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

import json
import time

from tempest.common import credentials_factory as common_creds
from tempest import config
from tempest.lib import exceptions
from tempest import test

from murano_tempest_tests import clients

CONF = config.CONF


class BaseServiceBrokerTest(test.BaseTestCase):
    """Base test class for Murano Service Broker API tests."""

    @classmethod
    def skip_checks(cls):
        super(BaseServiceBrokerTest, cls).skip_checks()
        if not CONF.service_broker.run_service_broker_tests:
            skip_msg = "Service Broker API tests are disabled"
            raise cls.skipException(skip_msg)
        if not CONF.service_available.murano_cfapi:
            skip_msg = "Service Broker API is disabled"
            raise cls.skipException(skip_msg)
        if not CONF.service_available.murano:
            skip_msg = "Murano is disabled"
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(BaseServiceBrokerTest, cls).setup_clients()
        if not hasattr(cls, "os_primary"):
            cls.username = CONF.identity.username
            cls.password = CONF.identity.password
            cls.tenant_name = CONF.identity.tenant_name
            cls.verify_nonempty(cls.username, cls.password, cls.tenant_name)
            cls.os_primary = clients.Manager()
        cls.service_broker_client = cls.os_primary.service_broker_client
        cls.application_catalog_client = \
            cls.os_primary.application_catalog_client

    @classmethod
    def get_client_with_isolated_creds(cls, type_of_creds="admin"):
        creds = cls.get_configured_isolated_creds(type_of_creds=type_of_creds)

        os = clients.Manager(credentials=creds)
        client = os.application_catalog_client

        return client

    @classmethod
    def get_configured_isolated_creds(cls, type_of_creds='admin'):
        identity_version = CONF.identity.auth_version
        if identity_version == 'v3':
            cls.admin_role = CONF.identity.admin_role
        else:
            cls.admin_role = 'admin'
        cls.credentials = common_creds.get_credentials_provider(
            name=cls.__name__,
            force_tenant_isolation=CONF.auth.use_dynamic_credentials,
            identity_version=CONF.identity.auth_version)
        if type_of_creds == 'primary':
            creds = cls.credentials.get_primary_creds()
        elif type_of_creds == 'admin':
            creds = cls.credentials.get_admin_creds()
        elif type_of_creds == 'alt':
            creds = cls.credentials.get_alt_creds()
        else:
            creds = cls.credentials.get_credentials(type_of_creds)
        cls.credentials.type_of_creds = type_of_creds

        return creds.credentials

    @classmethod
    def verify_nonempty(cls, *args):
        if not all(args):
            msg = "Missing API credentials in configuration."
            raise cls.skipException(msg)

    def wait_for_result(self, instance_id, timeout):
        start_time = time.time()
        start_status = self.service_broker_client.get_last_status(instance_id)
        while start_status:
            status = self.service_broker_client.get_last_status(instance_id)
            if status == start_status and time.time() - start_time > timeout:
                    raise exceptions.TimeoutException
            elif status != start_status:
                try:
                    parced_stat = status['state']
                    self.assertIn(str(parced_stat), ['succeeded', 'failed'])
                    result = str(parced_stat)
                    return result
                except KeyError:
                    parced_stat = json.loads(status)
                    self.assertIsInstance(parced_stat, dict)
                    result = parced_stat
                    return result
            else:
                time.sleep(2)

    def perform_deprovision(self, instance_id):
        self.service_broker_client.deprovision(instance_id)
        status = self.wait_for_result(instance_id, 30)
        self.assertEqual('succeeded', status)


class BaseServiceBrokerAdminTest(BaseServiceBrokerTest):

    @classmethod
    def setup_clients(cls):
        super(BaseServiceBrokerTest, cls).setup_clients()
        if not hasattr(cls, "os_admin"):
            cls.username = CONF.identity.username
            cls.password = CONF.identity.password
            cls.tenant_name = CONF.identity.tenant_name
            cls.verify_nonempty(cls.username, cls.password, cls.tenant_name)
            cls.os_admin = clients.Manager()
        cls.service_broker_client = cls.os_admin.service_broker_client
        cls.application_catalog_client = \
            cls.os_admin.application_catalog_client
