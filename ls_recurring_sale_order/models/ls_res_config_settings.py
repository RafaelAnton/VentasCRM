# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_config = fields.Selection([
        ('nothing_to_do', 'Create Only Quotation'),
        ('confirm', 'Create and Confirm Sale order'),
        ('confirm_invoice', 'Confirm Sale Order and Create Invoice')], string="Configuration for new sale order",
                              config_parameter='ls_sale_recurring_order.sale_config')

    when_sale_create = fields.Selection([
        ('on_confirm', 'After Confirm + Interval'),
        ('on_delivery','After Delivery + Interval')], string="When To create Next Sale Order",
                        config_parameter='ls_sale_recurring_order.when_sale_create')

    @api.onchange('sale_config')
    def onchange_sale_config(self):
        if self.sale_config=='confirm' or self.sale_config=='confirm_invoice':
            self.when_sale_create = 'on_delivery'

    @api.onchange('when_sale_create')
    def onchange_when_sale_create(self):
        if self.when_sale_create == 'on_confirm':
            self.sale_config = 'nothing_to_do'





