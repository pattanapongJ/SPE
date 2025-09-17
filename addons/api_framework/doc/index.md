# Enhance your **Odoo ERP Experience** with our powerful **Easy API Framework**

Explore the full capabilities of seamless integration through the Odoo API Framework, a revolutionary solution designed to elevate your Odoo experience. This no-code framework enables you to effortlessly expand Odoo's functionality to external systems. Immerse yourself in a realm of organized API interactions featuring adaptable authentication choices, straightforward JSON:API functionality, flexible GraphQL options, and secure resource access. More than just an API tool, it serves as the gateway to realizing the true potential of connectivity within Odoo.

## No-Code, **All Power**:

Easily enhance Odoo capabilities by seamlessly integrating external systems through our innovative Odoo API Framework. Engineered with a straightforward, no-code approach and a well-organized structure, this bundle simplifies communication between Odoo and external platforms, ensuring accessibility for all.

**Just configure and connect – it's that simple.**

## Framework **Simplicity**:
Our framework architecture provides a sturdy foundation for all your API needs. It's like building with Lego blocks – each module fits perfectly, offering a structured and organized way to manage API interactions.
**Just build and empower – it's that straightforward.**

## Diverse **Authentication** Options:
Choose from a spectrum of authentication methods, including API key, user-based, or OAuth2, custom-tailored to meet your security needs. Effortlessly establish and oversee access to your API resources without any hassle.
**Effortlessly configure and fortify – it's just that uncomplicated.**

## JSON:API Specification: https://jsonapi.org/
The included `easy_jsonapi` module allows you to handle all your API interactions using the JSON:API specification, making it a breeze to manage all aspects of reading, creating, updating, and deleting records in accordance with the JSON:API specification. Execute these operations seamlessly with straightforward queries, showcasing the power and simplicity of our solution.

**Open API based Dynamic all model documentation included within Odoo based on your installed things. No need to find fields from database or ugly forms.**
***Note: Custom models supported. Smile!***

> **What they says? {json:api}**
> If you’ve ever argued with your team about the way your JSON responses should be formatted, JSON:API can help you stop the bikeshedding and focus on what matters: your application.
> By following shared conventions, you can increase productivity, take advantage of generalized tooling and best practices. Clients built around JSON:API are able to take advantage of its features around efficiently caching responses, sometimes eliminating network requests entirely.

**Just query and conquer – it's that intuitive.**

## GraphQL Flexibility: https://graphql.org/
For those who crave flexibility, the `easy_graphql` module introduces GraphQL – a query language for APIs. Fetch exactly what you need, nothing more, with declarative data fetching. No more over-fetching or under-fetching – just precise data retrieval.

**`GraphiQL` within Odoo powered by dynamic models binding based on your installed things. Leverage GraphQL to precisely request API data, anticipate issues pre-query, and enhance code intelligence. It's smart querying for smarter coding. Just inquire and excel – it's that streamlined.**
***Note: Custom models supported here as well. Smile Again!***

> **What they says? GraphQL**
> A query language for your API
> GraphQL is a query language for APIs and a runtime for fulfilling those queries with your existing data. GraphQL provides a complete and understandable description of the data in your API, gives clients the power to ask for exactly what they need and nothing more, makes it easier to evolve APIs over time, and enables powerful developer tools.
> -- Ask for what you need, get exactly that
> -- Get many resources in a single request
> -- Describe what’s possible with a type system
> -- Move faster with powerful developer tools

**Just query and refine – it's that super amazing.**

## Custom Resource Access:
Manage access to your API resources without diving into code. The `api_resource_access` module allows easy configuration of who can access what, ensuring secure communication and controlled data flow.
**Simply set up and govern – it's that seamless.**

## Base API Structure:
Our base API structure provides the fundamental building blocks for your API system. While it can be used standalone for developers who want to roll their own, it truly shines when bundled with our complete framework, offering a plethora of features for robust API management.
**Just implement and excel – it's that foundational.**

Dive into the future of API management – simple, no-code, and structured. The **Odoo API Framework** is not just a tool; it's your partner in unleashing the true potential of seamless integration.

<br/><hr/><br/>

### Comprehensive Documentation: Odoo API Framework

#### Introduction

Welcome to the comprehensive documentation for the Odoo API Framework. This guide is tailored to enhance your understanding and utilization of the framework, offering a detailed walkthrough from installation to advanced configurations. The Odoo API Framework is a powerful tool designed to seamlessly integrate external systems with Odoo, providing a no-code approach to expand Odoo's functionality.

#### Installation

#### Prerequisites

Before embarking on the installation journey, make sure you have the following prerequisites in place:

- An active Odoo instance running version 16.0.
- Administrative access to the Odoo server.

##### Step-by-Step Installation Guide

1. **Download the Module:**
   Acquire the `api_framework` module exclusively from the official Odoo app store, our website, or by reaching out to us directly. Avoid obtaining the module from any other source, as it could jeopardize your Odoo environment or engage in malicious activities.

2. **Put in Addons Path and Restart Odoo:**
   Once you have the modules, put it in odoo addons path and restart your Odoo instance to apply the modules.

3. **Module Installation:**
   - Log in to your Odoo instance with administrative credentials.
   - Navigate to the Apps module.
   - Click on Update Apps List to ensure you have the latest modules.
   - Search for "API Framework" or "api_framework" and install the module.

**Congratulations! You've successfully installed the Odoo API Framework. Now, let's explore how to configure it.**

#### Configuration

##### Overview

The Odoo API Framework offers a balance of simplicity and flexibility in its configuration. Follow these steps to tailor the framework to your specific use cases:

1. **Access API Configuration Settings:**
   - In Odoo, navigate to API main menu.
   - Look for the API Settings menu. (You can create multiple api for different purpose or for different group of people all can be configured it's own way.)

2. **Authentication Options:**
   - Choose a name based on usage.
   - Define base path to access your api.
   - Choose from a variety of authentication methods, including API key, user-based, or OAuth2.
   - Effortlessly establish and oversee access to your API resources.
   - Click Open
   - Configure Users
   - Access Document and build your quary based on following need json:api or graphql.

#### JSON:API Quick Reference

JSON API is a standardized specification for building APIs in JSON format. This guide provides a quick reference on how to interact with JSON API, covering essential concepts and practical examples using various HTTP methods.

##### Getting Started

JSON API utilizes specific structures for API requests and responses, ensuring consistency and ease of use. To interact with a server, clients make requests to designated endpoints using standard HTTP methods, including GET, POST, PATCH, and DELETE.

##### Example Requests

###### GET Requests

1. **Sparse Fieldsets:** Retrieve specific fields for sale.order.

    ```
    GET /sale.order?fields[sale.order]=name,partner_id,date_order
    ```

2. **Including Related Resources:** Get sale.order and include the related partner_id.

    ```
    GET /sale.order?fields[sale.order]=partner_id&include=partner_id
    ```

3. **Pagination:** Get the second page of sale.order with 5 records per page.

    ```
    GET /sale.order?page[number]=2&page[size]=5
    ```

4. **Sort:** Get sale.order sorted by date_order in descending order.

    ```
    GET /sale.order?sort=-date_order
    ```

5. **Filter:** Get sale.order filtered by standard Odoo domain.

    ```
    GET /sale.order?filter=[AND, OR, ('state', '=', 'sale'), OR, ('state', '=', 'cancel'), ('team_id', '=', 5), OR, AND, ('amount_total', '>', 1000), ('team_id', '=', 1), OR, ('partner_id', '=', 11), ('user_id', '=', 6)]
    ```

6. Example Python Code for GET Request
    ```python
    import requests
    import json
    
    url = "https://your-api-endpoint.com/your-resource-endpoint"
    headers = {
      'Content-Type': 'application/vnd.api+json',
      'x-api-key': 'YOUR-API-KEY'
    }
    response = requests.get(url, headers=headers)
    print(response.text)
    ```

**For more information refer documentation on `easy_jsonapi` module.**
This quick reference provides a glimpse into interacting with JSON API, offering a structured approach for building powerful APIs. Developers can adapt these examples for their specific use cases, fostering consistency and efficiency in API interactions.
For more detailed information, refer to the JSON API Specification https://jsonapi.org/format/ .

#### GraphQL Quick Reference
GraphQL is a powerful query language for APIs that optimizes data fetching and provides a runtime for executing queries with existing data. This quick reference guide outlines fundamental concepts and showcases key GraphQL operations.

##### How It Works
GraphQL offers declarative data fetching, allowing clients to request precisely the data they need. With a hierarchical structure, queries mirror the shape of the response data, minimizing over-fetching and under-fetching common in REST APIs.
[GraphQL Specification](https://graphql.org/learn)

##### Query Operation

A GraphQL query is akin to a GET request in REST, enabling clients to read or fetch data from the server. Clients can specify desired data, and the server responds accordingly. Queries have a clear structure, as illustrated in the examples.

##### Read Records Example:

```gql
query MyQuery($offset: Int, $limit: Int, $order: String, $domain: [[Any]]) {
   ResPartner(offset: $offset, limit: $limit, order: $order, domain: $domain) {
      id
      name
      phone
      email
      is_company
      country_id {
         name
         code
      }
      user_id {
         name
         active
      }
      company_id {
         name
      }
   }
}
```

##### Read Single Record Example:

```gql
query MyQuery {
  ResPartner(id: "33") {
    id
    name
    phone
    email
    is_company
    country_id {
      name
      code
    }
    user_id {
      name
      active
    }
    company_id {
      name
    }
  }
}
```
##### Mutation Operation

GraphQL mutations modify data on the server, similar to POST, PUT, PATCH, or DELETE requests in REST. Mutations can create, update, or delete records.

##### Create Operation:

```gql
mutation Create {
    createResPartner: ResPartner(values: { ... }) {
        active
        category_id
        bank_ids
        city
        comment
        company_type
        id
        name
        phone
        mobile
        email
        street
        zip
    }
}
```

##### Update Operation:

```gql
mutation Update {
    updateResPartner: ResPartner(id: 96, values: { ... }) {
        active
        category_id
        bank_ids
        city
        comment
        company_type
        id
        name
        phone
        mobile
        email
        street
        zip
    }
}
```

##### Delete Operation:

```gql
mutation Delete {
    deleteResPartner: ResPartner(id: 96)
}
```

##### Method Execution

GraphQL supports method execution, allowing clients to trigger specific actions on the server.

```gql
mutation Method {
    methodSaleOrder: SaleOrder(id: 7, method_name: "action_draft", method_parameters: {})
}
```

**For more information refer documentation on easy_graphql module.**

This quick reference provides a glimpse into interacting with GraphQL API, offering a great approach for building powerful APIs. Developers can adapt these examples for their specific use cases, fostering consistency and efficiency in API interactions.
For more detailed information, refer to the GraphQL https://graphql.org/ .

### Contact us for any kind of help:

#### EKIKA CORPORATION PRIVATE LIMITED

##### Website: https://www.ekika.co

##### Phone/Whats APP: +91-9510031431

##### Email: hello@ekika.co
