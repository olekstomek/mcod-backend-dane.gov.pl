path "auth/approle/login" {
  capabilities = [ "create", "read" ]
}

path "database/*" {
  capabilities = [ "read" ]
}
