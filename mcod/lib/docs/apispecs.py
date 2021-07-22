# -*- coding: utf-8 -*-
from apispec import APISpec

rest_spec = APISpec(
    title='REST API',
    version='0.0.1',
    swagger="2.0",
    plugins=['apispec.ext.marshmallow']
)

rpc_spec = APISpec(
    title='RPC API',
    swagger="2.0",
    version='3',
    plugins=['apispec.ext.marshmallow']
)
