# Basic Authentication


## Introduction

HTTP Basic Authentication is a simple authentication scheme built into the HTTP protocol. It is based on challenge-response mechanism and is widely used for securing web applications and APIs. This document provides an overview of HTTP Basic Authentication, how it works, and examples of how to implement it.

## Format of Authorization Header

The Authorization header for HTTP Basic Authentication is constructed as follows:
```
Authorization: Basic base64(username:password)
```
The base64(username:password) is the base64 encoding of the concatenation of the username and password, separated by a colon (:).

**Headers**

|Key|Value|
|:-----------:|:----------------------------:|
|Authorization|Basic dXNlcm5hbWU6cGFzc3dvcmQ=|

## Example

**Here's an example using cURL:**
```
curl -X GET "https://api.example.com/resource" -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ="
```

**Here's an example using Python:**
```python
import requests

api_url = 'https://api.example.com/resource'

# Make an authenticated GET request
headers = {
    'Authorization': 'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
}

response = requests.get(api_url, headers=headers)
```

<img src="assets/Auth-Basic.png" class="img-fluid" alt="Auth-Basic"/>

## Configuring API-Basic Authentication

<img src="assets/API-Basic-Setting-1.png" class="img-fluid" alt="API-Basic-Authentication-Setting-1"/>

## References
 - [RFC 7617](https://datatracker.ietf.org/doc/html/rfc7617)
