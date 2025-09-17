# Easy Rest Json

## Introduction

This module’s support for Odoo’s JSON RESTful API format allows you to perform a variety of RPC operations with versatile authentication options, along with advanced framework features.

## How It Works

By defining a standard structure for API requests and responses, this module promotes consistency and ease of use. Below are several request examples:

### Configuring API

<img src="static/description/assets/images/API-Configuration-1.png" class="img-fluid" alt="Rest JSON Configuration"/>

### Requests

- **Search**

<img src="static/description/assets/images/search-request.png" class="img-fluid" alt="Rest JSON Search Request"/>

```python
import requests
import json

url = "http://localhost:8016/api-rest-json/res.partner/search"

payload = json.dumps({
  "args": [
    [
      [
        "is_company",
        "=",
        True
      ]
    ]
  ],
  "kwargs": {}
})
headers = {
  'Content-Type': 'application/json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```

- **Search Read**

<img src="static/description/assets/images/search-read-request.png" class="img-fluid" alt="Rest JSON Search Read Request"/>

```python
import requests
import json

url = "http://localhost:8016/api-rest-json/res.partner/search_read"

payload = json.dumps({
  "args": [
    [
      [
        "is_company",
        "=",
        True
      ]
    ]
  ],
  "kwargs": {
    "fields": [
      "name",
      "country_id",
      "comment",
      "is_company"
    ],
    "limit": 5
  }
})
headers = {
  'Content-Type': 'application/json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```

- **Search Count**

<img src="static/description/assets/images/search-count-request.png" class="img-fluid" alt="Rest JSON Search Count Request"/>

```python
import requests
import json

url = "http://localhost:8016/api-rest-json/res.partner/search_count"

payload = json.dumps({
  "args": [
    [
      [
        "is_company",
        "=",
        True
      ]
    ]
  ],
  "kwargs": {}
})
headers = {
  'Content-Type': 'application/json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```

- **Read**

<img src="static/description/assets/images/read-request.png" class="img-fluid" alt="Rest JSON Read Request"/>

```python
import requests
import json

url = "http://localhost:8016/api-rest-json/res.partner/read"

payload = json.dumps({
  "args": [
    [
      14,
      10,
      11
    ]
  ],
  "kwargs": {
    "fields": [
      "name",
      "country_id",
      "comment",
      "is_company"
    ]
  }
})
headers = {
  'Content-Type': 'application/json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

```

- **Read Group**

<img src="static/description/assets/images/read-group-request.png" class="img-fluid" alt="Rest JSON Read Group Request"/>

```python
import requests
import json

url = "http://localhost:8016/api-rest-json/res.partner/read_group"

payload = json.dumps({
  "args": [
    [
      [
        "is_company",
        "=",
        False
      ]
    ]
  ],
  "kwargs": {
    "fields": [
      "name",
      "country_id",
      "comment",
      "is_company"
    ],
    "groupby": "country_id"
  }
})
headers = {
  'Content-Type': 'application/json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```

- **Fields Get**

<img src="static/description/assets/images/fields-get-request.png" class="img-fluid" alt="Rest JSON Fields Get Request"/>

```python
import requests
import json

url = "http://localhost:8016/api-rest-json/res.partner/fields_get"

payload = json.dumps({
  "args": [],
  "kwargs": {
    "attributes": [
      "string",
      "help",
      "type"
    ]
  }
})
headers = {
  'Content-Type': 'application/json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```

- **Check Access Right**

<img src="static/description/assets/images/check-access-rights-request.png" class="img-fluid" alt="Rest JSON Check Access Rights Request"/>

```python
import requests
import json

url = "http://localhost:8016/api-rest-json/res.partner/check_access_rights"

payload = json.dumps({
  "args": [
    "create"
  ],
  "kwargs": {}
})
headers = {
  'Content-Type': 'application/json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

```

- **Create**

<img src="static/description/assets/images/create-request.png" class="img-fluid" alt="Rest JSON Create Request"/>

```python
import requests
import json

url = "http://localhost:8016/api-rest-json/res.partner/create"

payload = json.dumps({
  "args": [
    {
      "name": "Sample Partner",
      "email": "sample-partner@example.com"
    }
  ],
  "kwargs": {}
})
headers = {
  'Content-Type': 'application/json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```

- **Write**

<img src="static/description/assets/images/write-request.png" class="img-fluid" alt="Rest JSON Write Request"/>

```python
import requests
import json

url = "http://localhost:8016/api-rest-json/res.partner/write"

payload = json.dumps({
  "args": [
    [
      49
    ],
    {
      "name": "Sample Partner Change",
      "email": "sample-partner-change@example.com"
    }
  ],
  "kwargs": {}
})
headers = {
  'Content-Type': 'application/json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

```

- **Unlink**

<img src="static/description/assets/images/unlink-request.png" class="img-fluid" alt="Rest JSON Unlink Request"/>

```python
import requests
import json

url = "http://localhost:8016/api-rest-json/res.partner/unlink"

payload = json.dumps({
  "args": [
    [
      49
    ]
  ],
  "kwargs": {}
})
headers = {
  'Content-Type': 'application/json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```
