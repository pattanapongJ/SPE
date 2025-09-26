from odoo import SUPERUSER_ID, api
import logging

_logger = logging.getLogger(__name__)

# excute after installation
def update_existing_payment_terms(cr, registry):
    _logger.info("Starting update_existing_payment_terms")
    
    env = api.Environment(cr, SUPERUSER_ID, dict())
    account_bill_obj = env["account.billing"]
    account_bills = account_bill_obj.search([], order="id")
    
    _logger.info("Found %d account.billing records to update", len(account_bills))
    
    for bill_id in account_bills.ids:
        
        acc_bill = account_bills.browse(bill_id)
        
        sale_payment_term_id = acc_bill.partner_id.property_payment_term_id.id
        purchase_payment_term_id = acc_bill.partner_id.property_supplier_payment_term_id.id
        
        _logger.info("Processing bill ID %d: partner: %s, payment term: %s", bill_id, acc_bill.partner_id.name, acc_bill.partner_id.property_payment_term_id.name)
        
        if acc_bill.bill_type == 'out_invoice':
            if sale_payment_term_id:
                try:
                    cr.execute(
                        "UPDATE account_billing SET payment_terms_id = %s WHERE id = %s;",
                        (
                            sale_payment_term_id,
                            bill_id
                        )
                    )
                    _logger.info("Updated payment_terms_id for bill ID %d", bill_id)
                except Exception as e:
                    _logger.error("Failed to update payment_terms_id for bill ID %d: %s", bill_id, str(e))
            else:
                _logger.warning("No payment term ID for partner ID %d", sale_payment_term_id)
        else:
            if purchase_payment_term_id:
                try:
                    cr.execute(
                        "UPDATE account_billing SET payment_terms_id = %s WHERE id = %s;",
                        (
                            purchase_payment_term_id,
                            bill_id
                        )
                    )
                    _logger.info("Updated payment_terms_id for bill ID %d", bill_id)
                except Exception as e:
                    _logger.error("Failed to update payment_terms_id for bill ID %d: %s", bill_id, str(e))
            else:
                _logger.warning("No payment term ID for partner ID %d", purchase_payment_term_id)
                

    _logger.info("Finished post_init_hook")