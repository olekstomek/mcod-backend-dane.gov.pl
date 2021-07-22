# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import falcon
import jwt
from django.utils.translation import gettext_lazy as _

from mcod import settings
from mcod.lib.encoders import DateTimeToISOEncoder


def parse_auth_token(auth_header):
    if not auth_header:
        raise falcon.HTTPUnauthorized(
            title='401 Unauthorized',
            description=_('Missing Authorization Header'),
            code='token_error'
        )

    parts = auth_header.split()

    if parts[0].lower() != settings.JWT_HEADER_PREFIX.lower():
        raise falcon.HTTPUnauthorized(
            title='401 Unauthorized',
            description=_('Invalid Authorization Header'),
            code='token_error'
        )
    elif len(parts) == 1:
        raise falcon.HTTPUnauthorized(
            title='401 Unauthorized',
            description=_('Invalid Authorization Header: Token Missing'),
            code='token_error'
        )
    elif len(parts) > 2:
        raise falcon.HTTPUnauthorized(
            title='401 Unauthorized',
            description=_('Invalid Authorization Header: Contains extra content'),
            code='token_error'
        )

    return parts[1]


def decode_jwt_token(auth_header):
    token = parse_auth_token(auth_header=auth_header)

    options = dict(('verify_' + claim, True) for claim in settings.JWT_VERIFY_CLAIMS)

    options.update(
        dict(('require_' + claim, True) for claim in settings.JWT_REQUIRED_CLAIMS)
    )

    try:
        payload = jwt.decode(jwt=token, key=settings.JWT_SECRET_KEY,
                             options=options,
                             algorithms=settings.JWT_ALGORITHMS,
                             # issuer=settings.JWT_ISS,
                             # audience=settings.JWT_AUD,
                             leeway=settings.JWT_LEEWAY)
    except jwt.InvalidTokenError as ex:
        raise falcon.HTTPUnauthorized(
            title='401 Unauthorized',
            description=str(ex),
            code='token_error'
        )

    return payload


def get_auth_header(user, session_key, now=None, exp_delta=None):
    auth_token = get_auth_token(user, session_key, now=now, exp_delta=exp_delta)

    return '{header_prefix} {auth_token}'.format(
        header_prefix=settings.JWT_HEADER_PREFIX, auth_token=auth_token
    )


def get_auth_token(user, session_key, now=None, exp_delta=None):
    if not now:
        now = datetime.utcnow()

    discourse_api_key = user.discourse_api_key if user.has_access_to_forum else None
    discourse_user_name = user.discourse_user_name if user.has_access_to_forum else None

    payload = {
        'user': {
            'session_key': session_key,
            'email': user.email,
            'roles': user.system_roles,
            'discourse_user_name': discourse_user_name,
            'discourse_api_key': discourse_api_key
        }
    }

    exp_delta = exp_delta if exp_delta else settings.JWT_EXPIRATION_DELTA

    if 'iat' in settings.JWT_VERIFY_CLAIMS:
        payload['iat'] = now

    if 'nbf' in settings.JWT_VERIFY_CLAIMS:
        payload['nbf'] = now + timedelta(seconds=settings.JWT_LEEWAY)

    if 'exp' in settings.JWT_VERIFY_CLAIMS:
        payload['exp'] = now + timedelta(seconds=exp_delta)

    return jwt.encode(payload, settings.JWT_SECRET_KEY,
                      json_encoder=DateTimeToISOEncoder).decode('utf-8')
