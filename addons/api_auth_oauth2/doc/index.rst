API OAuth2
==========

Introduction
------------

This module includes the authorization-code-grant flow of OAuth2 for API access.

How It Works
------------

**Authorization and Token Related Steps:**

- First, the client registers the redirect URI, which is provided in the API record form, with the respective provider.
- The client must make a request to ``/auth/oauth2/provider/authorize`` with its ``client_id`` in the request body (JSON format), which returns an authorization URL in the response's JSON body.
- When the client uses this authorization URL, it must authorize with its respective user. After successful authorization, the server returns token information, which includes:
  - ``access_token``, ``refresh_token``, ``expires_in``, ``expires_at``, ``scope``, ``token_type``, ``id_token``. *Note: This may vary between providers.*
  - ``db``, ``login``
- If the client wants to refresh the token and obtain a new access token, it must make a request to ``/auth/oauth2/token`` with its ``client_id`` and ``client_user_identity`` in the request body (JSON format). This returns new token-related information.
- If the client wants to revoke the token, it must make a request to ``/auth/oauth2/revoke`` with its ``client_id`` and ``client_user_identity`` in the request body (JSON format). This revokes the token from the authorization server and also deletes the client API user record.

**API Resource Access Steps:**

- When a client wants to fetch API data using **OAuth2**, it should make an HTTP request with the header: ``Authorization: Bearer <access_token_value>``.
- If the ``access_token`` is valid, the response data is returned. If the ``access_token`` is invalid, the client must refresh the token or authorize the user again.

For More Details
----------------

Python Request Examples:
------------------------

**1. Client Authorization:**

.. code-block:: python

    import requests
    import json

    url = "https://api-15.dev.odoo-apps.ekika.co/auth/oauth2/provider/authorize"

    payload = json.dumps({
      "client_id": "YOUR_CLIENT_ID",
      "client_user_identity": "YOUR_UNIQUE_CLIENT_IDENTITY",
      "api_endpoint": "YOUR_API_ENDPOINT"
    })
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)

**2. Refresh Token:**

.. code-block:: python

    import requests
    import json

    url = "https://api-15.dev.odoo-apps.ekika.co/auth/oauth2/token"

    payload = json.dumps({
      "client_id": "YOUR_CLIENT_ID",
      "client_user_identity": "YOUR_UNIQUE_CLIENT_IDENTITY",
      "api_endpoint": "YOUR_API_ENDPOINT"
    })
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

**3. Revoke Token:**

.. code-block:: python

    import requests
    import json

    url = "https://api-15.dev.odoo-apps.ekika.co/auth/oauth2/revoke"

    payload = json.dumps({
      "client_id": "YOUR_CLIENT_ID",
      "client_user_identity": "YOUR_UNIQUE_CLIENT_IDENTITY",
      "api_endpoint": "YOUR_API_ENDPOINT"
    })
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)

Configuring API-OAuth2 Authentication
-------------------------------------

.. image:: static/description/assets/API-OAuth2-Setting-1.png
   :class: img-fluid
   :alt: API-OAuth2-Authentication-Setting-1

.. image:: static/description/assets/API-OAuth2-Setting-2.png
   :class: img-fluid
   :alt: API-OAuth2-Authentication-Setting-2

.. image:: static/description/assets/API-OAuth2-Setting-3.png
   :class: img-fluid
   :alt: API-OAuth2-Authentication-Setting-3
