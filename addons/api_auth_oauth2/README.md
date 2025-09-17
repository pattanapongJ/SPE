# Api Oauth2

## Introduction

This module include authorization-code-grant flow of OAuth2 for API. 

## How It Works
**Auhtorization and Token Related Steps:**
- First, client register redirect-uri, which is provided in api record form, to its respected provider 
- client has to made request to "*/auth/oauth2/provider/authorize*" with its *client_id* in request-body(json), which returns authorization_url in json-body from response
- when client use this authorization_url, client has to authorize with its respected user, after successful authorization server returns token information, which includes:
  - access_token, refresh_token, expires_in, expires_at, scope, token_type, id_token. *Note: this differs from provider*
  - db, login
- if client wants to refresh the token & get access-token then made request to "*/auth;/oauth2/token*" with its *client-id*, *client-user-identity* in request-body(json), which return new token related information
- if client wants to revoke the token then made request to "*auth/oauth2/revoke*" with its *client-id*, *client-user-identity* in request-body(json), which revoke the token from authorization server and also delete the client api user record.


**API Resource Access Steps:**
- when client want fetch api data using **oauth2** method, made http-request using header: ``Authorization: Bearer access_token_value``
- if access_token in valid then it return response data. and if access_token invalid then client has to refresh the token or authorize the user again. 

## For More Details

## Python Request Examples:
**1. Client Authorization:**
```python
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
```

**2. Refresh Token:**
```python
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
```

**3. Revoke Token:**
```python
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
```

## Configuring API-OAuth2 Authentication

<img src="assets/API-OAuth2-Setting-1.png" class="img-fluid" alt="API-OAuth2-Authentication-Setting-1"/>

<img src="assets/API-OAuth2-Setting-2.png" class="img-fluid" alt="API-OAuth2-Authentication-Setting-2"/>

<img src="assets/API-OAuth2-Setting-3.png" class="img-fluid" alt="API-OAuth2-Authentication-Setting-3"/>
