# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools import float_round
from odoo.exceptions import UserError


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    product_qty = fields.Float(string='Quantity', default=1.0000,digits=(16,4), required=True)

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    rounding = fields.Float(string='Rounding Precision', default=0.0100,digits=(16,4))

    def explode(self, product, quantity, picking_type=False):
        """
            Explodes the BoM and creates two lists with all the information you need: bom_done and line_done
            Quantity describes the number of times you need the BoM: so the quantity divided by the number created by the BoM
            and converted into its UoM
        """
        from collections import defaultdict
        for rec in self :
            graph = defaultdict(list)
            V = set()

            def check_cycle(v, visited, recStack, graph):
                visited[v] = True
                recStack[v] = True
                for neighbour in graph[v]:
                    if visited[neighbour] == False:
                        if check_cycle(neighbour, visited, recStack, graph) == True:
                            return True
                    elif recStack[neighbour] == True:
                        return True
                recStack[v] = False
                return False

            product_ids = set()
            product_boms = {}
            def update_product_boms():
                products = rec.env['product.product'].browse(product_ids)
                product_boms.update(rec._get_product2bom(products, bom_type='phantom',
                    picking_type=picking_type or rec.picking_type_id, company_id=rec.company_id.id))
                # Set missing keys to default value
                for product in products:
                    product_boms.setdefault(product, rec.env['mrp.bom'])

            boms_done = [(rec, {'qty': quantity, 'product': product, 'original_qty': quantity, 'parent_line': False})]
            lines_done = []
            V |= set([product.product_tmpl_id.id])

            bom_lines = []
            for bom_line in rec.bom_line_ids:
                product_id = bom_line.product_id
                V |= set([product_id.product_tmpl_id.id])
                graph[product.product_tmpl_id.id].append(product_id.product_tmpl_id.id)
                bom_lines.append((bom_line, product, quantity, False))
                product_ids.add(product_id.id)
            update_product_boms()
            product_ids.clear()
            while bom_lines:
                current_line, current_product, current_qty, parent_line = bom_lines[0]
                bom_lines = bom_lines[1:]

                if current_line._skip_bom_line(current_product):
                    continue

                line_quantity = current_qty * current_line.product_qty
                if not current_line.product_id in product_boms:
                    update_product_boms()
                    product_ids.clear()
                bom = product_boms.get(current_line.product_id)
                if bom:
                    rounding = rec.rounding
                    converted_line_quantity = current_line.product_uom_id._compute_quantity(line_quantity / bom.product_qty, bom.product_uom_id)
                    # We Rounding up Here
                    converted_line_quantity = float_round(converted_line_quantity, precision_rounding=rounding, rounding_method='UP')
                    bom_lines += [(line, current_line.product_id, converted_line_quantity, current_line) for line in bom.bom_line_ids]
                    for bom_line in bom.bom_line_ids:
                        graph[current_line.product_id.product_tmpl_id.id].append(bom_line.product_id.product_tmpl_id.id)
                        if bom_line.product_id.product_tmpl_id.id in V and check_cycle(bom_line.product_id.product_tmpl_id.id, {key: False for  key in V}, {key: False for  key in V}, graph):
                            raise UserError(_('Recursion error!  A product with a Bill of Material should not have itself in its BoM or child BoMs!'))
                        V |= set([bom_line.product_id.product_tmpl_id.id])
                        if not bom_line.product_id in product_boms:
                            product_ids.add(bom_line.product_id.id)
                    boms_done.append((bom, {'qty': converted_line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': current_line}))
                else:
                    # We round up here because the user expects that if he has to consume a little more, the whole UOM unit
                    # should be consumed.
                    # rounding = current_line.product_uom_id.rounding
                    rounding = rec.rounding
                    line_quantity = float_round(line_quantity, precision_rounding=rounding, rounding_method='UP')
                    lines_done.append((current_line, {'qty': line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': parent_line}))

            return boms_done, lines_done

