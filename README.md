# hashi_vault_inventory

A dynamic inventory script for ansible to lookup entries in hashicorp vault

This inventory uses vault and reads from a KV2 path, secrets are added as ansible hosts, key/values in the secrets are added as vars.

- Notes:

  - Dynamic inventory plugin as per [ansible docs](https://docs.ansible.com/ansible/2.10/dev_guide/developing_inventory.html)

  - Env vars __VAULT_ADDR__, and __VAULT_CERT__ must be set for this inventory to work.

  - If you wish to use a vault token for auth set VAULT_TOEKN environment variable, for approle auth use: __ANSIBLE_HASHI_VAULT_ROLE_ID__ & __ANSIBLE_HASHI_VAULT_SECRET_ID__
      this should help keep in line with the community.hashi_vault plugins.

  - To use this please create a inventory yaml in your repo names 'inventory_vault.yml' with the following example data:

    ```yaml
    ---
    plugin: sirance.inventory_vault.inventory_vault
    vault_secret_path: <service-contract-name>
    ```

  - To test use `ansible-inventory -i inventory_vault.yml --graph --vars -v`
