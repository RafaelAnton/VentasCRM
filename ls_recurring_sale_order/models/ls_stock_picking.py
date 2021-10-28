# -*- coding: utf-8 -*-
from odoo import models, fields, api,_


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def button_validate(self):
        """
        Default Base Method for validate picking.
        :return: Super
        """
        res = super(StockPicking, self).button_validate()

        if isinstance(res, bool):
            next_order = self.env['ir.config_parameter'].sudo().get_param('ls_sale_recurring_order.when_sale_create')
            if next_order and next_order == 'on_delivery':
                for pw_picking in self:
                    if pw_picking.picking_type_code == 'outgoing' and pw_picking.sale_id:
                        if pw_picking.sale_id:
                            recurring_order_id = pw_picking.sale_id.recurring_order_id
                            if recurring_order_id:
                                for rso in recurring_order_id:
                                    rso.generate_sale_order()
        return res
