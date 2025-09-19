from odoo.tests.common import TransactionCase

class TestSaleOrder(TransactionCase):

    def setUp(self, *args, **kwargs):
        super(TestSaleOrder, self).setUp(*args, **kwargs)
        self.test_order = self.env['sale.order'].create({'partner_id': 8,
                                                         'order_line': [
                                                                            ( 0,0,
                                                                                {
                                                                                    "name": "Test --- Arduino CPU (WiFi 2.4G, Humidity Sensor)",
                                                                                    "product_id": 119,
                                                                                    "product_uom_qty": 1.0,
                                                                                    "product_uom": 1,
                                                                                    "price_unit": 666.0,
                                                                                }
                                                                            )
                                                                        ]
                                                         })
        self.assertEqual(self.test_order.name, '********* create ***** sale order ***************')

    def test_button_confirm(self):
        """Make available button"""
        self.test_order.action_confirm()
        self.assertEqual(self.test_order.state, '******************* confirm sale order ***************')


