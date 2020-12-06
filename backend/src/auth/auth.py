import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'cbhuber.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffeeshop'

# AuthError Exception


class AuthError(Exception):
    ''' AuthError Exception
        A standardized way to communicate auth failure modes. '''

    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

# -----------------------------------------------------------------------------------------------------------

# Auth Header


def get_token_auth_header():
    ''' Attempts to get the header from the request.
        Raises an AuthError if no header is present.
        Attempts to split bearer and the token.
        Raises an AuthError if the header is malformed.
        Returns the token part of the header. '''

    # Check for auth in header
    if 'Authorization' not in request.headers:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization missing in header.'
        }, 401)

    # Grab the headers in a list
    auth_headers = request.headers['Authorization'].split(' ')

    # Check for proper formatting
    if len(auth_headers) != 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Header malformed.'
        }, 401)

    # Make sure it is a bearer token
    if auth_headers[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Bearer type missing.'
        }, 401)

    # Return the token
    return auth_headers[1]

# -----------------------------------------------------------------------------------------------------------


def check_permissions(permission, payload):
    ''' @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

        !!NOTE check and confirm the RBAC settings are enabled in Auth0.
        Raises an AuthError if permissions are not included in the payload.
        Raises an AuthError if the requested permission string is not in the payload permissions array.
        Returns true otherwise. '''

    # Ensure the contents have the permissions to check
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_jwt',
            'description': 'Permissions not in decoded JWT.'
        }, 400)

    # Ensure permission is in the actual payload
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'invalid_jwt',
            'description': f'Permission: {permission} not in decoded JWT.'
        }, 401)

    return True

# -----------------------------------------------------------------------------------------------------------


def verify_decode_jwt(token):
    ''' @INPUTS
        token: a json web token (string), it is an Auth0 token with key id (kid).

        Verifies the token using Auth0 /.well-known/jwks.json
        Decodes the payload from the token and validates the claims.
        Returns the decoded payload. '''

    # Get the public key from Auth0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())

    # Get the data in the header
    unverified_header = jwt.get_unverified_header(token)

    # Choose the proper key
    rsa_key = {}

    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    # Verify the key
    if rsa_key:

        try:
            # Use the key to verify the jwt
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)

        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)

    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key.'
    }, 400)


# -----------------------------------------------------------------------------------------------------------


def requires_auth(permission=''):
    ''' @INPUTS
        permission: string permission (i.e. 'post:drink')

        Uses the get_token_auth_header method to get the token.
        Uses the verify_decode_jwt method to decode the jwt.
        Uses the check_permissions method validate claims and check the requested permission.
        Returns the decorator which passes the decoded payload to the decorated method. '''
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except:

                raise AuthError({
                    'code': 'invalid_jwt_payload',
                    'description': 'Unauthorized.'
                }, 401)

            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
