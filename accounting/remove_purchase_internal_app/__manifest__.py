# -*- coding: utf-8 -*-

{
	'name': "Remove Internal Reference from Purchase Order Line Odoo App",
	'author': "Edge Technologies",
	'version': "14.0.1.0",
	'live_test_url':'https://youtu.be/3rLs98Ts-B4',
    "images":["static/description/main_screenshot.png"],
    "license" : "OPL-1",
	'summary': "Remove product internal reference from purchase order line hide code from purchase description remove code from purchase order lines description hide product code from purchase order line hide product code from po line description remove product code po",
	'description':	"""
            This odoo app helps user to remove product internal reference/code from purchase order lines description.

			In odoo product internal reference/code will automatically added to purchase order line description, and user need to remove it manually if user wants to add more description for product. this app will remove internal reference from purchase order line description.
					""",
	'depends': ['base', 'purchase'],
	'data': [],
	'demo': [],
	'qweb': [],
	'installable': True,
	'auto_install': False,
	'application': False,
	"price": 5,
	"currency": 'EUR',
	'category': "Purchase",
}
