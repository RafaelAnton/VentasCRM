# -*- coding: utf-8 -*-
from odoo import models, fields, api,_


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    recurring_order_id = fields.Many2one('recurring.order', string="Recurring Order",copy=False)


    def action_confirm(self):
        """
        Default Base Method for confirm order.
        :return: Super
        """
        action_confirm_res = super(SaleOrder, self).action_confirm()
        next_order = self.env['ir.config_parameter'].sudo().get_param('ls_sale_recurring_order.when_sale_create')
        if next_order and next_order=='on_confirm' and self.recurring_order_id and not self._context.get('no_rso',False):
            self.recurring_order_id.generate_sale_order()
        return action_confirm_res