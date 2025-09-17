Odoo RESTful API Bundle v1.0
============================

:Author: Anand Shukla
:Company: EKIKA Corporation Private Limited
:Support: https://ekika.co/support
:Phone: +91-9510031431
:Email: hello@ekika.co
:Skype: amshukla17
:Published: Dec 16, 2023
:Last Update: April 21, 2024
:Version: v1.0
:Odoo Version: 15.0, 16.0, 17.0
:Doc Update: April 21, 2024

Introduction
------------
The Odoo RESTful API Bundle simplifies integrating external applications with your Odoo ERP system. It offers a modular framework, allowing you to build Dynamic and Custom APIs tailored to your specific needs. This documentation guides you through installation, configuration, and using the API Bundle's functionalities.


Why this API Bundle?
--------------------

* **Dynamic Connectivity**: Effortlessly connect your APIs to Odoo models and fields.
* **Modular Design**: Build custom APIs with a flexible, building-block approach.
* **Multiple APIs and Endpoints**: Create and manage multiple APIs within a single Odoo environment/database and beyond.
* **Authentication Options**: Select from various authentication methods like API keys, Basic Auth, Standard User Credentials or OAuth2 Authentication.
* **Comprehensive Documentation**: Access clear documentation for each module within the bundle.
* **Redoc**: Open API specification based documentation of Json:API you configure.
* **Introspection**: GraphQL Introspection within Odoo for documentation of GraphQL APIs you configure.
* **Postman Collection**: https://git.ekika.co/EKIKA.co/Odoo-API-Framework-POSTMAN-Collection
* **Flutter Sample**: Contact us to get easy to build mobile applications with the source code.
* **Expert Support**: Receive exceptional support from the EKIKA team.

Two types of API Specifications:
--------------------------------

1. GraphQL (`Know more about GraphQL here <https://apps.odoo.com/apps/modules/17.0/easy_graphql/>`_)
2. JSON:API Specification v1.1 (`Know more about JSON:API <https://apps.odoo.com/apps/modules/17.0/easy_jsonapi/>`_)
3. *More to come like odoo standard jsonrpc, xmlrpc supported with api framework architecture, gRPC, Webhooks, Subscriptions, Custom etc.*
4. *You can implement your own too.*

Four Types of Authentication:
-----------------------------

1. API-Key Based Authentication (`know more <https://apps.odoo.com/apps/modules/17.0/api_auth_apikey/>`_)
2. Basic Authentication (`know more <https://apps.odoo.com/apps/modules/17.0/api_auth_basic/>`_)
3. Standard User Credentials Authentication (`know more <https://apps.odoo.com/apps/modules/17.0/api_auth_apiuser/>`_)
4. OAuth2 Authentication (`know more <https://apps.odoo.com/apps/modules/17.0/api_auth_oauth2/>`_)

Three Types of Access Controls:
-------------------------------

1. Standard User Based Access (`supported from foundation <https://apps.odoo.com/apps/modules/17.0/api_framework_base/>`_)
2. Sudo User Access (`supported from foundation <https://apps.odoo.com/apps/modules/17.0/api_framework_base/>`_)
3. Custom Managed API Specific User Access (`know more <https://apps.odoo.com/apps/modules/17.0/api_resource_access/>`_)


NOTE
~~~~

**How and Which modules you should Buy?**

If you do not want everything in a bundle and want to save based on your need, then do not spend more. You can buy separate apps based on your purpose. Let me tell you how you should buy OR contact us so we can suggest what you should buy.

**Examples:**

1. Suppose You want to use API-Key authentication and Json:API specification for RESTful APIs. Just buy the following apps. When you add the following two apps in your cart you will have 5 apps in the cart and you have to spend less compare to price of full bundle.
    * `Odoo Json API <https://apps.odoo.com/apps/modules/17.0/easy_jsonapi/>`_
    * `API Key Based Authentication <https://apps.odoo.com/apps/modules/17.0/api_auth_apikey/>`_

2. Similar way if you only need graphql and Basic Authentication add the following two apps in your cart.
    * `Odoo GraphQL API <https://apps.odoo.com/apps/modules/17.0/easy_graphql/>`_
    * `API Basic Authentication <https://apps.odoo.com/apps/modules/17.0/api_auth_basic/>`_

You will have full control on your APIs from a single database. You can make more than 20+ flavors of API using this framework with version 1.0. We are already enhancing this framework so request your needs to us. We do not charge for any generic usable developments around APIs. Contact Us for your specific needs. skype:- amshukla17

Contact us for your query: https://ekika.co/support

Getting Started
---------------

Installation
~~~~~~~~~~~~

1. **Download the Module:**
   Acquire the `api_framework` module exclusively from the official Odoo app store, our website, or by reaching out to us directly. Avoid obtaining the module from any other source, as it could jeopardize your Odoo environment or engage in malicious activities.

2. **Put in Addons Path and Restart Odoo:**
   Once you have the modules, put it in the odoo addons path and restart your Odoo instance to apply the modules.

3. **Module Installation:**
   * Log in to your Odoo instance with administrative credentials.
   * Navigate to the Apps module.
   * Click on the Update Apps List to ensure you have the latest modules.
   * Search for "API Framework" or "api_framework" and install the module.

**Congratulations! You've successfully installed the Odoo API Framework. Now, let's explore how to configure it.**

Configuration and Overview
~~~~~~~~~~~~~~~~~~~~~~~~~~

The Odoo API Framework offers a balance of simplicity and flexibility in its configuration. Follow these steps to tailor the framework to your specific use cases:

1. **Access API Configuration Settings:**

   * In Odoo, navigate to the API main menu. (If you do not find allow access of API administration to your user.)
   * Look for the API Settings menu. (You can create multiple api for different purposes or for different groups of people all can be configured it's own way.)

2. **API Setup and Authentication Options:**

   * Choose a name based on usage.
   * Define a base path to access your api.
   * Choose from a variety of authentication methods, including API key, user-based, or OAuth2.
   * Effortlessly establish and oversee access to your API resources.
   * Click Open
   * Configure Users
   * Access Document and build your query based on following needs json:api or graphql.

**For detailed information you have to read documentation done on each module we provided below.**

**Protocol / API specification:**

* Json:API: `Documentation <https://apps.odoo.com/apps/modules/17.0/easy_jsonapi>`_ and follow this specification `jsonapi.org <https://jsonapi.org/format/>`_
* GraphQL: `Documentation <https://apps.odoo.com/apps/modules/17.0/easy_graphql>`_

**Authentication:**

* API Key Based Authentication: `Documentation <https://apps.odoo.com/apps/modules/17.0/api_auth_apikey>`_
* API OAuth2 Authentication: `Documentation <https://apps.odoo.com/apps/modules/17.0/api_auth_oauth2>`_
* API User Based Authentication: `Documentation <https://apps.odoo.com/apps/modules/17.0/api_auth_apiuser>`_
* API Basic Authentication: `Documentation <https://apps.odoo.com/apps/modules/17.0/api_auth_basic>`_

**Access:**

* Personalize API Specific Access: `Documentation <https://apps.odoo.com/apps/modules/17.0/api_resource_access/>`_

Do not buy `Odoo API Base <https://apps.odoo.com/apps/modules/17.0/api_framework_base/>`_ as a single app it just has framework style approach for foundation to maintain API Framework building block. It is very useful if you are a advance level principal developer. Otherwise we do not recommend purchasing this base app as a single item.

Do not remove dependent apps from cart after adding one app. It may be possible you do not get what you are expecting, instead contact us. We are happy to save your budget.

**We believe in building strong partnerships with our customers. Let us help you unlock the full potential of your Odoo implementation. Contact EKIKA today for a free consultation and see how we can streamline your workflows.**