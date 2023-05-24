# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google ID Token helpers.

Provides support for verifying `OpenID Connect ID Tokens`_, especially ones
generated by Google infrastructure.

To parse and verify an ID Token issued by Google's OAuth 2.0 authorization
server use :func:`verify_oauth2_token`. To verify an ID Token issued by
Firebase, use :func:`verify_firebase_token`.

A general purpose ID Token verifier is available as :func:`verify_token`.

Example::

    from google.oauth2 import _id_token_async
    from google.auth.transport import aiohttp_requests

    request = aiohttp_requests.Request()

    id_info = await _id_token_async.verify_oauth2_token(
        token, request, 'my-client-id.example.com')

    if id_info['iss'] != 'https://accounts.google.com':
        raise ValueError('Wrong issuer.')

    userid = id_info['sub']

By default, this will re-fetch certificates for each verification. Because
Google's public keys are only changed infrequently (on the order of once per
day), you may wish to take advantage of caching to reduce latency and the
potential for network errors. This can be accomplished using an external
library like `CacheControl`_ to create a cache-aware
:class:`google.auth.transport.Request`::

    import cachecontrol
    import google.auth.transport.requests
    import requests

    session = requests.session()
    cached_session = cachecontrol.CacheControl(session)
    request = google.auth.transport.requests.Request(session=cached_session)

.. _OpenID Connect ID Token:
    http://openid.net/specs/openid-connect-core-1_0.html#IDToken
.. _CacheControl: https://cachecontrol.readthedocs.io
"""

import json
import os

import six
from six.moves import http_client

from google.auth import environment_vars
from google.auth import exceptions
from google.auth import jwt
from google.auth.transport import requests
from google.oauth2 import id_token as sync_id_token


async def _fetch_certs(request, certs_url):
    """Fetches certificates.

    Google-style cerificate endpoints return JSON in the format of
    ``{'key id': 'x509 certificate'}``.

    Args:
        request (google.auth.transport.Request): The object used to make
            HTTP requests. This must be an aiohttp request.
        certs_url (str): The certificate endpoint URL.

    Returns:
        Mapping[str, str]: A mapping of public key ID to x.509 certificate
            data.
    """
    response = await request(certs_url, method="GET")

    if response.status != http_client.OK:
        raise exceptions.TransportError(
            "Could not fetch certificates at {}".format(certs_url)
        )

    data = await response.content()

    return json.loads(data)


async def verify_token(
    id_token,
    request,
    audience=None,
    certs_url=sync_id_token._GOOGLE_OAUTH2_CERTS_URL,
    clock_skew_in_seconds=0,
):
    """Verifies an ID token and returns the decoded token.

    Args:
        id_token (Union[str, bytes]): The encoded token.
        request (google.auth.transport.Request): The object used to make
            HTTP requests. This must be an aiohttp request.
        audience (str): The audience that this token is intended for. If None
            then the audience is not verified.
        certs_url (str): The URL that specifies the certificates to use to
            verify the token. This URL should return JSON in the format of
            ``{'key id': 'x509 certificate'}``.
        clock_skew_in_seconds (int): The clock skew used for `iat` and `exp`
            validation.

    Returns:
        Mapping[str, Any]: The decoded token.
    """
    certs = await _fetch_certs(request, certs_url)

    return jwt.decode(
        id_token,
        certs=certs,
        audience=audience,
        clock_skew_in_seconds=clock_skew_in_seconds,
    )


async def verify_oauth2_token(
    id_token, request, audience=None, clock_skew_in_seconds=0
):
    """Verifies an ID Token issued by Google's OAuth 2.0 authorization server.

    Args:
        id_token (Union[str, bytes]): The encoded token.
        request (google.auth.transport.Request): The object used to make
            HTTP requests. This must be an aiohttp request.
        audience (str): The audience that this token is intended for. This is
            typically your application's OAuth 2.0 client ID. If None then the
            audience is not verified.
        clock_skew_in_seconds (int): The clock skew used for `iat` and `exp`
            validation.

    Returns:
        Mapping[str, Any]: The decoded token.

    Raises:
        exceptions.GoogleAuthError: If the issuer is invalid.
    """
    idinfo = await verify_token(
        id_token,
        request,
        audience=audience,
        certs_url=sync_id_token._GOOGLE_OAUTH2_CERTS_URL,
        clock_skew_in_seconds=clock_skew_in_seconds,
    )

    if idinfo["iss"] not in sync_id_token._GOOGLE_ISSUERS:
        raise exceptions.GoogleAuthError(
            "Wrong issuer. 'iss' should be one of the following: {}".format(
                sync_id_token._GOOGLE_ISSUERS
            )
        )

    return idinfo


async def verify_firebase_token(
    id_token, request, audience=None, clock_skew_in_seconds=0
):
    """Verifies an ID Token issued by Firebase Authentication.

    Args:
        id_token (Union[str, bytes]): The encoded token.
        request (google.auth.transport.Request): The object used to make
            HTTP requests. This must be an aiohttp request.
        audience (str): The audience that this token is intended for. This is
            typically your Firebase application ID. If None then the audience
            is not verified.
        clock_skew_in_seconds (int): The clock skew used for `iat` and `exp`
            validation.

    Returns:
        Mapping[str, Any]: The decoded token.
    """
    return await verify_token(
        id_token,
        request,
        audience=audience,
        certs_url=sync_id_token._GOOGLE_APIS_CERTS_URL,
        clock_skew_in_seconds=clock_skew_in_seconds,
    )


async def fetch_id_token(request, audience):
    """Fetch the ID Token from the current environment.

    This function acquires ID token from the environment in the following order.
    See https://google.aip.dev/auth/4110.

    1. If the environment variable ``GOOGLE_APPLICATION_CREDENTIALS`` is set
       to the path of a valid service account JSON file, then ID token is
       acquired using this service account credentials.
    2. If the application is running in Compute Engine, App Engine or Cloud Run,
       then the ID token are obtained from the metadata server.
    3. If metadata server doesn't exist and no valid service account credentials
       are found, :class:`~google.auth.exceptions.DefaultCredentialsError` will
       be raised.

    Example::

        import google.oauth2._id_token_async
        import google.auth.transport.aiohttp_requests

        request = google.auth.transport.aiohttp_requests.Request()
        target_audience = "https://pubsub.googleapis.com"

        id_token = await google.oauth2._id_token_async.fetch_id_token(request, target_audience)

    Args:
        request (google.auth.transport.aiohttp_requests.Request): A callable used to make
            HTTP requests.
        audience (str): The audience that this ID token is intended for.

    Returns:
        str: The ID token.

    Raises:
        ~google.auth.exceptions.DefaultCredentialsError:
            If metadata server doesn't exist and no valid service account
            credentials are found.
    """
    # 1. Try to get credentials from the GOOGLE_APPLICATION_CREDENTIALS environment
    # variable.
    credentials_filename = os.environ.get(environment_vars.CREDENTIALS)
    if credentials_filename:
        if not (
            os.path.exists(credentials_filename)
            and os.path.isfile(credentials_filename)
        ):
            raise exceptions.DefaultCredentialsError(
                "GOOGLE_APPLICATION_CREDENTIALS path is either not found or invalid."
            )

        try:
            with open(credentials_filename, "r") as f:
                from google.oauth2 import _service_account_async as service_account

                info = json.load(f)
                if info.get("type") == "service_account":
                    credentials = service_account.IDTokenCredentials.from_service_account_info(
                        info, target_audience=audience
                    )
                    await credentials.refresh(request)
                    return credentials.token
        except ValueError as caught_exc:
            new_exc = exceptions.DefaultCredentialsError(
                "GOOGLE_APPLICATION_CREDENTIALS is not valid service account credentials.",
                caught_exc,
            )
            six.raise_from(new_exc, caught_exc)

    # 2. Try to fetch ID token from metada server if it exists. The code works
    # for GAE and Cloud Run metadata server as well.
    try:
        from google.auth import compute_engine
        from google.auth.compute_engine import _metadata

        request_new = requests.Request()
        if _metadata.ping(request_new):
            credentials = compute_engine.IDTokenCredentials(
                request_new, audience, use_metadata_identity_endpoint=True
            )
            credentials.refresh(request_new)
            return credentials.token
    except (ImportError, exceptions.TransportError):
        pass

    raise exceptions.DefaultCredentialsError(
        "Neither metadata server or valid service account credentials are found."
    )
