#!/usr/bin/env sh

vault status
if [ "$?" -eq "0" ]
then
    exit 0
fi

initialized=true
vault operator init --status

if [ "$?" -ne "0" ]
then
  initialized=false
fi

if [ "$initialized" == false ]
then
  vault operator init > /vault/secrets/keys.file || true
fi

export VAULT_TOKEN=$(grep 'Initial Root Token:' /vault/secrets/keys.file | awk '{print substr($NF, 1, length($NF))}')

vault operator unseal -address=${VAULT_ADDR} $(grep 'Key 1:' /vault/secrets/keys.file | awk '{print $NF}')
vault operator unseal -address=${VAULT_ADDR} $(grep 'Key 2:' /vault/secrets/keys.file | awk '{print $NF}')
vault operator unseal -address=${VAULT_ADDR} $(grep 'Key 3:' /vault/secrets/keys.file | awk '{print $NF}')

if [ "$initialized" == false ]
then
    vault secrets enable database
    vault write database/config/mcod plugin_name=postgresql-database-plugin allowed_roles="mcod" connection_url="postgresql://{{username}}:{{password}}@172.18.18.18:5432/mcod?sslmode=disable" username="mcod" password="mcod"
    vault write database/roles/mcod db_name=mcod creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN ENCRYPTED PASSWORD '{{password}}' VALID UNTIL '{{expiration}}' IN ROLE mcod INHERIT NOCREATEROLE NOCREATEDB NOSUPERUSER NOREPLICATION;" default_ttl="10m" max_ttl="24h"
    vault read database/creds/mcod
    vault auth enable approle
    vault policy write backend /vault/policies/policy.hcl
    vault write auth/approle/role/backend policies=backend
    vault read auth/approle/role/backend/role-id
    vault write -f auth/approle/role/backend/secret-id
fi

vault operator init --status

if [ "$?" -ne "0" ]
then
    exit 1
fi

exit $?