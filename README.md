# hashi_vault_inventory
Dynamic inventory script for ansible to lookup entries in hashicorp vault

This inventory uses vault and reads from a KV2 path
    
- notes:

    - Dynamic inventory plugin as per https://docs.ansible.com/ansible/2.10/dev_guide/developing_inventory.html
    
    - Env vars 'VAULT_TOKEN', 'VAULT_URL', 'VAULT_AUTH' and 'VAULT_CERT' must be set for this inventory to work.
    
    - To use this please create a inventory yaml in your repo names 'inventory_vault.yml' with the following example data:
        
        ```
        ---
        plugin: inventory_vault
        vault_secret_path: <service-contract-name>
        ```

    - To test use `ansible-inventory -i inventory_vault.yml --graph --vars -v`