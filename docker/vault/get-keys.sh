#!/usr/bin/env sh

vault status
if [ "$?" -ne "0" ]
then
    echo "Vault is sealed!"
    exit 1
fi

export VAULT_TOKEN=$(grep 'Initial Root Token:' /vault/secrets/keys.file | awk '{print substr($NF, 1, length($NF))}')

vault read auth/approle/role/backend/role-id
vault write -f auth/approle/role/backend/secret-id
