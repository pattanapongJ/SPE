# EKIKA API Framework Multi-Database

## Overview

The **EKIKA API Framework Multi-Database** module enables API requests in an Odoo environment with multiple databases. This module allows clients to specify the target database for an API call using request headers or query parameters.

## Features

- Supports API calls in multi-database environments.
- Detects the target database dynamically from request headers or query parameters.
- Ensures seamless integration with the EKIKA REST API framework.

## Installation

### 1. Add the module to server-wide modules

Modify your **Odoo configuration file** (e.g., `odoo.conf`) to include `api_header_db` in the `server_wide_modules` parameter:

```ini
server_wide_modules = base,web,api_header_db
```

### 2. Restart Odoo

After modifying the configuration file, restart the Odoo server:

```sh
sudo systemctl restart odoo
```

or if running manually:

```sh
./odoo-bin -c /path/to/odoo.conf
```

## Usage

When making an API request, specify the target database by passing one of the following headers or query parameters:

### Headers (Preferred Method)
Include one of these headers in your request:

```http
INSTANCE: <Your Database Name>
DB: <Your Database Name>
DATABASE: <Your Database Name>
```

### Query Parameters (Alternative Method)
Alternatively, you can pass the database name as a query parameter:

```http
GET /api/some-endpoint?instance=<Your Database Name>
```

## Example Request

```bash
curl -X GET "https://yourdomain.com/api/some-endpoint" \
     -H "INSTANCE: my_database" \
     -H "Authorization: Bearer <your_token>"
```

This ensures that the API request is executed in the specified database context.

## Compatibility
- Odoo **14.0**

## License

This module is licensed under the **Odoo Proprietary License v1 (OPL-1)**.

## Author

**EKIKA CORPORATION PRIVATE LIMITED**  
Website: [https://ekika.co](https://ekika.co)

For support or inquiries, please contact [support@ekika.co](mailto:support@ekika.co).

