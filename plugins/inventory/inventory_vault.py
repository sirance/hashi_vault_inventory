# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    inventory: inventory_vault.py
    author: 
        - Simon Rance <sirance@gmail.com>
    version_added: "1.1"
    short_description: Dynamic inventory for using vault with ansible
    description:
        - This inventory uses vault and reads from a KV2 path
    notes:
        - "Dynamic inventory plugin as per https://docs.ansible.com/ansible/2.10/dev_guide/developing_inventory.html"
        - ""
        - "Env vars 'VAULT_TOKEN', 'VAULT_URL', 'VAULT_AUTH' and 'VAULT_CERT' must be set for this inventory to work."
        - ""
        - "To use this please create a inventory yaml in your repo names 'inventory_vault.yml' with the following example data:"
        - "---"
        - "plugin: inventory_vault"
        - "vault_secret_path: <service-contract-name>"
        - ""
        - "To test use `ansible-inventory -i inventory_vault.yml --graph --vars -v`"
'''
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.parsing.yaml.objects import AnsibleSequence
from ansible.utils.display import Display

import os
import hvac
import requests
import yaml

display = Display()

class InventoryModule(BaseInventoryPlugin):

    NAME = 'inventory_vault'

    def verify_file(self, path):
        ''' return true/false if this is possibly a valid file for this plugin to consume '''
        valid = False
        if super(InventoryModule, self).verify_file(path):
            # base class verifies that file exists and is readable by current user
            if path.endswith('inventory_vault.yaml') or path.endswith('inventory_vault.yml'):
                valid = True
        return valid


    def parse(self, inventory, loader, path, cache=True):
        ''' Ansible method to generate the inventory '''
        # call base method to ensure properties are available for use with other helper methods
        super(InventoryModule, self).parse(inventory, loader, path, cache)

        # Check env vars are set correctly
        vault_url = os.environ.get('VAULT_URL')
        vault_token = os.environ.get('VAULT_TOKEN')
        vault_cert = os.environ.get('VAULT_CERT')
        

        if vault_url is None:
            raise AnsibleParserError("Please ensure VAULT_URL is set in your environment")

        if vault_token is None:
            raise AnsibleParserError("Please ensure VAULT_AUTH is set in your environment")

        if vault_cert is None:
            raise AnsibleParserError("Please ensure VAULT_CERT is set in your environment")


        config = self._read_config_data(path)
        if config.get('vault_secret_path', None) is None:
            raise AnsibleParserError("Please ensure 'vault_secret_path' is set in your inventory_pac.yml")


        # Connect to vault
        vault_client = hvac.Client(
        url=vault_url,
        )
        if vault_cert:
        # When use a self-signed certificate for the vault service itself, we need to
        # include our local ca bundle here for the underlying requests module.
                rs = requests.Session()
                vault_client.session = rs
                rs.verify = vault_cert

        # login_response = vault_client.auth.ldap.login(
        #     username=vault_user,
        #     password=vault_pass,
        # )
        # vault_client.token = load_vault_token(vault_client)
        vault_client.token = vault_token

        if not vault_client.is_authenticated():
                error_msg = 'Unable to authenticate to the Vault service'
                raise hvac.exceptions.Unauthorized(error_msg)


        config_vault_mount_point = config['vault_mount_point']
        config_vault_secret_path = config['vault_secret_path']
        path_group = config_vault_secret_path.split('/')[-1]
        path_group = self.inventory.add_group(path_group)
        list_response = vault_client.secrets.kv.v2.list_secrets(
                mount_point=config_vault_mount_point, 
                path=config_vault_secret_path,
                )
        list_of_hosts = list_response['data']['keys']
        for hosts in list_of_hosts:
            if "/" in hosts:
                continue
            list_vars = vault_client.secrets.kv.v2.read_secret_version(
                mount_point=config_vault_mount_point,
                path=config_vault_secret_path + "/" + hosts,
            )
            self.inventory.add_host(hosts)
            for key in list_vars['data']['data'].keys():
                self.inventory.set_variable(hosts, key, list_vars['data']['data'][key])
            self.inventory.add_child(path_group, hosts)
