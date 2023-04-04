# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    inventory: inventory_vault.py
    author: 
        - Simon Rance <sirance@gmail.com>
    version_added: "1.0.4"
    short_description: Dynamic inventory for using vault with ansible
    description:
        - This inventory uses vault and reads from a KV2 path
    notes:
        - "Dynamic inventory plugin as per https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html"
        - ""
        - "VAULT_ADDR & VAULT_CACERT environment varaible must always be available."
        - ""
        - "Available auth methods as follows, along with required variables."
        - "Token: 'VAULT_TOKEN'" 
        - ""
        - "AppRole: 'ANSIBLE_HASHI_VAULT_ROLE_ID' & 'ANSIBLE_HASHI_VAULT_SECRET_ID'"
        - ""
        - "JWT: 'ANSIBLE_HASHI_VAULT_JWT' & 'ANSIBLE_HASHI_VAULT_JWT_ROLE'"
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
import certifi
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

        vault_url = os.environ.get('VAULT_ADDR')
        vault_cert = os.environ.get('VAULT_CACERT')
        if vault_url is None:
            raise AnsibleParserError("Please ensure VAULT_ADDR is set in your environment")

        if vault_cert is None:
            raise AnsibleParserError("Please ensure VAULT_CACERT is set in your environment")

        config = self._read_config_data(path)
        if config.get('vault_secret_path', None) is None:
            raise AnsibleParserError("Please ensure 'vault_secret_path' is set in your inventory_pac.yml")

        # Test for SSL errors, and add custom CA to certifi if errors are raised:
        try:
            test = requests.get(vault_url)
        except requests.exceptions.SSLError as err:
            cafile = certifi.where()
            with open(vault_cert, 'rb') as infile:
                customca = infile.read()
            with open(cafile, 'ab') as outfile:
                outfile.write(customca)

        if "VAULT_TOKEN" in os.environ:
            vault_token = os.environ.get('VAULT_TOKEN')
            if vault_token is None:
                raise AnsibleParserError("Please ensure VAULT_TOKEN is set in your environment")

            # Connect to vault
            vault_client = hvac.Client(
            url=vault_url,
            )
            vault_client.token = vault_token
            if not vault_client.is_authenticated():
                error_msg = 'Unable to authenticate to the Vault service'
                raise hvac.exceptions.Unauthorized(error_msg)
        elif "ANSIBLE_HASHI_VAULT_ROLE_ID" in os.environ:
            vault_role_id = os.environ.get('ANSIBLE_HASHI_VAULT_ROLE_ID')
            vault_secret_id = os.environ.get('ANSIBLE_HASHI_VAULT_SECRET_ID')
            if vault_role_id is None:
                raise AnsibleParserError("Please ensure ANSIBLE_HASHI_VAULT_ROLE_ID and ANSIBLE_HASHI_VAULT_SECRET_ID are set in your environment")
            if vault_secret_id is None:
                raise AnsibleParserError("Please ensure ANSIBLE_HASHI_VAULT_ROLE_ID and ANSIBLE_HASHI_VAULT_SECRET_ID are set in your environment")
            
            # Connect to vault
            vault_client = hvac.Client(
                url=vault_url,
            )
            vault_client.auth.approle.login(
                role_id=vault_role_id,
                secret_id=vault_secret_id
            )
            if not vault_client.is_authenticated():
                error_msg = 'Unable to authenticate to the Vault service'
                raise hvac.exceptions.Unauthorized(error_msg)
        elif "ANSIBLE_HASHI_VAULT_JWT" in os.environ:
            vault_jwt = os.environ.get('ANSIBLE_HASHI_VAULT_JWT')
            vault_jwt_role = os.environ.get('ANSIBLE_HASHI_VAULT_JWT_ROLE')
            if vault_jwt is None:
                raise AnsibleParserError("Please ensure ANSIBLE_HASHI_VAULT_JWT is set in your environment")
            if vault_jwt_role is None:
                raise AnsibleParserError("Please ensure ANSIBLE_HASHI_VAULT_JWT_ROLE is set in your environment")
            vault_client = hvac.Client(
                url=vault_url,
            )
            vault_client.auth.jwt.jwt_login(
                role=vault_jwt_role,
                jwt=vault_jwt
            )
            if not vault_client.is_authenticated():
                error_msg = 'Unable to authenticate to the Vault service'
                raise hvac.exceptions.Unauthorized(error_msg)
        else :
            raise AnsibleParserError("Please ensure VAULT_TOKEN or ANSIBLE_HASHI_VAULT_ROLE_ID and ANSIBLE_HASHI_VAULT_SECRET_ID are set in your environment")

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
