# { json:api }

## Introduction

JSON API is a specification for building APIs (Application Programming Interfaces) in JSON format. It provides guidelines for how client applications can request and receive data from a server. [**Know more**](https://jsonapi.org/format/1.1/)

## How It Works
JSON API works by defining a specific structure for API requests and responses, allowing for consistency and ease of use. Here's how it works:

### Request:

 1. **Endpoint:** Clients make requests to specific endpoints (URLs) on the server to retrieve or manipulate resources. For example, a client might request a list of articles from the "/articles" endpoint.
 2. **HTTP Methods:** JSON API uses standard HTTP methods like GET, POST, PATCH, and DELETE for different operations. GET is used to retrieve data, POST to create new resources, PATCH to update existing resources, and DELETE to remove resources.
 3. **Parameters:** Clients can include query parameters in the request URL to specify filtering, sorting, pagination, sparse fieldsets, or include related resources. For instance, clients can request only specific fields of a resource, or request related data to be included in the response.

### Example of a JsonAPI Requests:
 - **GET Requests:**
1. **Sparse Fieldsets:** Get sale.order with only the "name", "partner_id", "date_order" fields included in the response.
    ```
    GET /sale.order?fields[sale.order]=name,partner_id,date_order
    ```
2. **Including Related Resources:** Get sale.order and include the related partner_id in the response.
    ```
    /sale.order?fields[sale.order]=partner_id&include=partner_id
    ```
3. **Pagination:** Get the second page of sale.order with 5 records per page.
    ```
    GET /sale.order?page[number]=2&page[size]=5
    ```
4. **Sort:**  Get sale.order sorted by their date_order in descending order.
    ```
    GET /sale.order?sort=-date_order
    ```
4. **Filter:**  Get sale.order filter by standard odoo domain, consider below example.
    ```
    GET /sale.order?filter=[AND, OR, ('state', '=', 'sale'), OR, ('state', '=', 'cancel'), ('team_id', '=', 5), OR, AND, ('amount_total', '>', 1000), ('team_id', '=', 1), OR, ('partner_id', '=', 11), ('user_id', '=', 6)]
    ```
- **Read Records Example:**

<img src="assets/JsonAPI-Read.png" class="img-fluid" alt="JsonAPI-Read"/>

```python
import requests
import json

url = "https://easyapi.ekika.app/user-jsonapi-apikey/res.partner?fields[res.partner]=name,is_company,email,phone,country_id,user_id,company_id&fields[res.country]=name,code&fields[res.users]=name,active&include=country_id,user_id,company_id&fields[res.company]=name&page[number]=1&page[size]=5&sort=name,-id&filter=[('is_company', '=', true)]"

payload = {}
headers = {
  'Content-Type': 'application/vnd.api+json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

```

- **Read Single Record Example:**

<img src="assets/JsonAPI-Read-Single-Record.png" class="img-fluid" alt="JsonAPI-Read-Single-Record"/>

```python
import requests
import json

url = "https://easyapi.ekika.app/user-jsonapi-apikey/res.partner/33?fields[res.partner]=name,is_company,email,phone,country_id,user_id,company_id&fields[res.country]=name,code&fields[res.users]=name,active&include=country_id,user_id,company_id&fields[res.company]=name"

payload = {}
headers = {
  'Content-Type': 'application/vnd.api+json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

```

 - **POST Requests:**
- **Create Request Example:**

<img src="assets/JsonAPI-Create.png" class="img-fluid" alt="JsonAPI-Create"/>


```python
import requests
import json

url = "https://easyapi.ekika.app/user-jsonapi-apikey/res.partner"

payload = json.dumps({
  "data": {
    "type": "res.partner",
    "attributes": {
      "active": True,
      "name": "Ekika Corporation",
      "company_type": "company",
      "city": "Gandhinagar",
      "street": "Gandhinagar",
      "zip": "382421",
      "comment": "<p>Comment Here</p>",
      "phone": "5554444555444",
      "mobile": "1010101",
      "website": "http://www.ekika.co",
      "email": "hello@ekika.co"
    },
    "relationships": {
      "category_id": {
        "data": [
          {
            "type": "res.partner.category",
            "id": "4"
          },
          {
            "type": "res.partner.category",
            "id": "3"
          }
        ]
      },
      "bank_ids": {
        "data": [
          {
            "type": "res.partner.bank",
            "attributes": {
              "sequence": 10,
              "bank_id": 2,
              "acc_number": "11212121212",
              "allow_out_payment": True,
              "acc_holder_name": False
            }
          },
          {
            "type": "res.partner.bank",
            "attributes": {
              "sequence": 11,
              "bank_id": 3,
              "acc_number": "3434343434343434",
              "allow_out_payment": True,
              "acc_holder_name": False
            }
          }
        ]
      }
    }
  }
})
headers = {
  'Content-Type': 'application/vnd.api+json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

```

- **PATCH Requests:**

- **Update Request Example:**

<img src="assets/JsonAPI-Update.png" class="img-fluid" alt="JsonAPI-Update"/>

```python
import requests
import json

url = "https://easyapi.ekika.app/user-jsonapi-apikey/res.partner/1061"

payload = json.dumps({
  "data": {
    "type": "res.partner",
    "id": 1061,
    "attributes": {
      "active": True,
      "name": "Ekika Corporation Pvt Ltd.",
      "company_type": "company",
      "city": "Gandhinagar",
      "street": "Gandhinagar",
      "zip": "000000",
      "comment": "<p>Comment Here</p>",
      "phone": "5554444555444",
      "mobile": "1010101",
      "website": "http://www.ekika.co",
      "email": "hello@ekika.co"
    },
    "relationships": {
      "category_id": {
        "data": []
      },
      "bank_ids": {
        "data": [
          {
            "type": "res.partner.bank",
            "id": 26,
            "attributes": {
              "sequence": 25,
              "bank_id": 2,
              "acc_number": "999999",
              "allow_out_payment": True,
              "acc_holder_name": False
            }
          }
        ]
      }
    }
  }
})
headers = {
  'Content-Type': 'application/vnd.api+json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("PATCH", url, headers=headers, data=payload)

print(response.text)

```

- **DELETE Requests:**

- **Delete Request Example:**

<img src="assets/JsonAPI-Delete.png" class="img-fluid" alt="JsonAPI-Delete"/>

```python
import requests
import json

url = "https://easyapi.ekika.app/user-jsonapi-apikey/res.partner/1061"

payload = {}
headers = {
  'Content-Type': 'application/vnd.api+json',
  'x-api-key': 'YOUR-API-KEY'
}

response = requests.request("DELETE", url, headers=headers, data=payload)

print(response.text)

```

## References:
- [**Visit Json-API Specification**](https://jsonapi.org/format/1.1/)
