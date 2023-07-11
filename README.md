# hashi_vault_inventory  - v.1.0.5

A dynamic inventory script for ansible to lookup entries in hashicorp vault

This inventory uses vault and reads from a KV2 path, secrets are added as ansible hosts, key/values in the secrets are added as vars. If a key of service exists, the host is also grouped under that value.

## Usage

```VAULT_ADDR``` & V```AULT_CACERT``` environment varaible must always be available.

Available auth methods as follows, along with required variables:

| Auth | Variables |
| ----|----|
| Token | ```VAULT_TOKEN```|
|AppRole | ```ANSIBLE_HASHI_VAULT_ROLE_ID``` and ```ANSIBLE_HASHI_VAULT_SECRET_ID```|
|JWT | ```ANSIBLE_HASHI_VAULT_JWT``` and  ```ANSIBLE_HASHI_VAULT_JWT_ROLE```|

To use this please create a inventory yaml in your repo names __inventory_vault.yml__ with the following example data:

```yaml
---
plugin: inventory_vault
vault_mount_point: <kv mount>
vault_secret_path: <secret path used for inventory>
```

To test use ```ansible-inventory -i inventory_vault.yml --graph --vars -v```
