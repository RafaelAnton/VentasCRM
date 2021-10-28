# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import date
from odoo.exceptions import AccessError, UserError, ValidationError
from .ls_get_date import get_intervals_from_dates


class RecurringOrder(models.Model):
    _name = 'recurring.order'
    _rec_name = "sequence"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    sequence = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                           states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    name = fields.Char(string="Name")
    partner_id = fields.Many2one('res.partner', string="Customer")
    partner_invoice_id = fields.Many2one(
        "res.partner", string="Invoice Address", tracking=True)
    partner_shipping_id = fields.Many2one(
        "res.partner", string="Delivery Address", tracking=True)
    interval = fields.Integer(string="Interval",required=True,default=1)
    interval_option = fields.Selection(selection=[('days', 'days'),
                                                  ('weeks', 'weeks'),
                                                  ('months', 'months'),
                                                  ('years', 'years')], string='Interval unit', default='days',
                                       help='Time unit for the Interval')
    start_date = fields.Date(string="Start Date",required=True,default=lambda self: fields.Date.today())
    end_date = fields.Date(string="End Date",required=True)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('running', 'Running'),
        ('expired', 'Expired'),
        ('complete', 'Complete'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=1,
        help="If you change the pricelist, only newly added lines will be affected.")
    currency_id = fields.Many2one(related='pricelist_id.currency_id', depends=["pricelist_id"], store=True)
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, tracking=2,
                              default=lambda self: self.env.user)
    recurring_order_lines = fields.One2many('recurring.order.line', 'recurring_order_id', string="Order Lines")
    sale_count = fields.Integer(string="Sales", compute="_compute_child_order_ids")
    sale_order_ids = fields.Many2many('sale.order', string="Sale Orders")
    reference = fields.Char(string="Reference")
    hide_button = fields.Boolean("Hide Button", compute="get_value_for_hide_button", store=True)
    show_update_pricelist = fields.Boolean(string='Has Pricelist Changed',
                                           help="Technical Field, True if the pricelist was changed;\n"
                                                " this will then display a recomputation button")
    sale_confirm_order = fields.Integer(
        "Confirmed Sale Order", compute='_compute_child_order_ids', tracking=True)

    @api.constrains('start_date','end_date','interval')
    def check_dates(self):
        """
        This Method is used for Check Normal constraints for start date, end date and interval
        :return: Raise Validation Error
        """
        if self.start_date and self.start_date < fields.Date.today():
            raise ValidationError(_("Start date must be greater than today."))
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError(_("End date must be greater than Start date."))
        if not self.interval:
            raise ValidationError(_("Interval must be greater than 0."))
        if self.interval and self.interval < 1:
            raise ValidationError(_("Interval must be greater than 0."))

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id(self):
        """
        Set boolean value on change of price list if need to recalculate product price or not
        :return:
        """
        if self.recurring_order_lines and self.pricelist_id:
            self.show_update_pricelist = True
        else:
            self.show_update_pricelist = False

    @api.depends('partner_id')
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Use for setting invoice address and delivery address onchange partner id.
        :return: None
        """
        if self.partner_id:
            self.update({'partner_invoice_id': self.partner_id,
                         'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
                         'partner_shipping_id': self.partner_id})

    def _compute_child_order_ids(self):
        for order in self:
            order.sale_count = self.env['sale.order'].search_count(
                [('recurring_order_id', '=', order.id)])
            order.sale_confirm_order = self.env['sale.order'].search_count(
                [('recurring_order_id', '=', order.id), ('state', '=', 'sale'), ('picking_ids.state', '!=', 'done')])

    def update_prices(self):
        self.ensure_one()
        lines_to_update = []
        for line in self.recurring_order_lines:
            product = line.product_id.with_context(
                partner=self.partner_id,
                quantity=line.product_uom_qty,
                date=self.start_date,
                pricelist=self.pricelist_id.id,
                uom=line.product_uom.id
            )
            price_unit = self.env['account.tax']._fix_tax_included_price_company(
                line._get_display_price(product), line.product_id.taxes_id, line.tax_id, line.company_id)
            if self.pricelist_id.discount_policy == 'without_discount' and price_unit:
                discount = max(0, (price_unit - product.price) * 100 / price_unit)
            else:
                discount = 0
            lines_to_update.append((1, line.id, {'price_unit': price_unit, 'discount': discount}))
        self.update({'recurring_order_lines': lines_to_update})
        self.show_update_pricelist = False
        self.message_post(body=_("Product prices have been recomputed according to pricelist <b>%s<b> ", self.pricelist_id.display_name))

    @api.depends('sale_order_ids', 'sale_order_ids.date_order')
    def get_value_for_hide_button(self):
        for rec in self:
            if rec.sale_order_ids:
                list_date = get_intervals_from_dates(rec.start_date, rec.end_date, rec.interval, rec.interval_option)
                print(list_date)
                p_dates = rec.sale_order_ids.mapped('date_order')
                present_dates = []
                for da in p_dates:
                    present_dates.append(da.date())
                new_list = [item for item in list_date if item not in present_dates]
                remain_ = list(set(list_date) - set(present_dates))
                if not len(remain_):
                    rec.hide_button = True
                    rec.write({'state': 'complete'})
                else:
                    rec.hide_button = False
            else:
                rec.hide_button = False

    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(
                    _('You can not delete a running or complete recurring order. You must first cancel it.'))
        return super(RecurringOrder, self).unlink()

    def action_cancel(self):
        """
        This Method Will cancle the Recurring order and depending sale order if applicable.
        :return: True
        """
        res = True
        for rso in self:
            for order in rso.sale_order_ids:
                for invoice in order.invoice_ids.filtered(
                        lambda inv: inv.payment_state not in ['paid', 'in_payment', 'partial'] and inv.state == 'post'):
                    invoice.button_draft()
                    invoice.button_cancel()
                if not order.invoice_ids.filtered(lambda inv: inv.payment_state in ['paid', 'in_payment', 'partial']):
                    res = order.with_context(
                        {'disable_cancel_warning': True, 'order_creation': 'do_no_create'}).action_cancel()
            rso.state = 'cancel'
        return res

    def action_draft(self):
        """
        Change the State of recurring order
        :return:
        """
        return self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        # import pdb; pdb.set_trace()
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('sequence', _('New')) == _('New'):
            seq_date = None
            vals['sequence'] = self.env['ir.sequence'].next_by_code('recurring.order') or _('New')
        return super().create(vals)

    def action_cron_auto_update_recurring(self):
        """
        This Method will check if recurring order is expried or not via cron.
        :return: None
        """
        orders = self.env['recurring.order'].search([])
        for order in orders:
            if order.end_date < date.today():
                order.write({
                    'state': 'expired',
                })

    def create_manual_sale_order(self):
        """
        This Method will used for create manual or extra sale order for that particular recurring order.
        :return:
        """
        action = {}
        lines = []
        for line in self.recurring_order_lines:
            order_line = (0, 0, {'product_id': line.product_id.id,
                                 'name': line.product_id.name,
                                 'product_uom': line.product_id.uom_id.id,
                                 'product_uom_qty': line.product_uom_qty,
                                 'price_unit': line.price_unit,
                                 'discount': line.discount})
            lines.append(order_line)
        default_dict = {'default_recurring_order_id': self.id, 'default_partner_id': self.partner_id.id,
                        'default_order_line': lines,
                        'default_partner_shipping_id': self.partner_shipping_id.id,
                        'default_partner_invoice_id': self.partner_invoice_id.id}
        action['view_mode'] = 'form'
        action['res_model'] = 'sale.order'
        action['target'] = 'new'
        action['type'] = 'ir.actions.act_window'
        action['view_id'] = self.env.ref('sale.view_order_form').id
        action['context'] = default_dict
        return action

    def generate_sale_order(self):
        """
        This Method will create sale order based on configuration on click on generate rfq.
        :return: None
        """
        self.ensure_one()
        recurring_lines = self.mapped('recurring_order_lines')
        list_date = get_intervals_from_dates(self.start_date, self.end_date, self.interval, self.interval_option)
        p_dates = self.sale_order_ids.mapped('date_order')
        present_dates = []
        for da in p_dates:
            present_dates.append(da.date())
        new_list = [item for item in list_date if item not in present_dates]
        remain_ = list(set(list_date) - set(present_dates))
        if len(remain_):
            self.write({
                'state': 'running',
            })
            order = self.create_order(new_list[0], recurring_lines)
            self.sale_order_ids += order
            return True
            # return {
            #     'domain': "[('id', '=', %s)]" % order.id,
            #     'view_type': 'form',
            #     'view_mode': 'form',
            #     'res_model': 'sale.order',
            #     'context': self.env.context,
            #     'res_id': order.id,
            #     'view_id': [self.env.ref('sale.view_order_form').id],
            #     'type': 'ir.actions.act_window',
            #     'nodestroy': True
            # }

    @api.model
    def _prepare_sale_order_vals(self, recurring, date):
        """
        This Method will used for preparing the sale order vals.
        :param recurring: current recurring order
        :param date: date of order
        :return: dict: order vals
        """
        order_vals = {
            'date_order': date,
            'origin': recurring.name,
            'partner_id': recurring.partner_id.id,
            'state': 'draft',
            'company_id': recurring.company_id.id,
            'recurring_order_id': recurring.id,
            # 'fiscal_position_id': self.env['account.fiscal.position'].with_context(
            #     company_id=recurring.company_id.id).get_fiscal_position(recurring.partner_id.id),
            'payment_term_id': recurring.partner_id.property_supplier_payment_term_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
        }
        order_vals['user_id'] = recurring.user_id.id
        return order_vals

    @api.model
    def _prepare_sale_order_line_vals(self, recurrent_line, order):
        """
        This Method will used for preparing the sale order line vals.
        :param recurrent_line: current recurring order line
        :param order: sale order id
        :return: dict: order line vals
        """
        product_lang = recurrent_line.product_id.with_context({
            'lang': order.partner_id.lang,
            'partner_id': order.partner_id.id,
        })
        fpos = order.fiscal_position_id
        order_line_vals = {
            'order_id': order.id,
            'company_id': order.company_id.id,
            'product_id': recurrent_line.product_id.id,
            'product_uom_qty': recurrent_line.product_uom_qty or 1.0,
            'price_unit': recurrent_line.price_unit,
            'product_uom': recurrent_line.product_id.uom_id.id or recurrent_line.product_id.uom_id.id,
            'name': product_lang.display_name,
            'tax_id': fpos.map_tax(
                recurrent_line.product_id.taxes_id.filtered(lambda r: r.company_id.id == self.company_id.id))
        }
        # if recurrent_line.specific_price:
        #     order_line_vals['price_unit'] = recurrent_line.specific_price
        order_line_vals['tax_id'] = [(6, 0, tuple(order_line_vals['tax_id']))]
        # if recurrent_line.additional_description:
        #     order_line_vals['name'] += " %s" % (recurrent_line.additional_description)
        return order_line_vals

    def create_order(self, date, recurrent_lines):
        """
        This Method will create sale order based on recurring order line
        :param date: order date
        :param recurrent_lines: recurring order line
        :return: object: new created sale order
        """
        self.ensure_one()
        order_line_obj = self.env['sale.order.line'].with_context(
            company_id=self.company_id.id)
        order_vals = self._prepare_sale_order_vals(self, date)
        order = self.env['sale.order'].create(order_vals)
        for recurrent_line in recurrent_lines:
            order_line_vals = self._prepare_sale_order_line_vals(
                recurrent_line, order)
            newline = order_line_obj.create(order_line_vals)
            newline.product_id_change()
            sale_order_state = self.env['ir.config_parameter'].sudo().get_param('ls_sale_recurring_order.sale_config')
            if sale_order_state:
                if sale_order_state=='confirm':
                    order.with_context(no_rso = True).action_confirm()
                if sale_order_state=='confirm_invoice':
                    order.action_confirm()
                    order._create_invoices()
        return order

    def action_view_sale_orders(self):
        """
        This method will used for view of sale orders which are on this recurring order
        :return: dict: action
        """
        sale_orders = self.mapped('sale_order_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        if len(sale_orders) > 1:
            action['domain'] = [('id', 'in', sale_orders.ids)]
        elif len(sale_orders) == 1:
            form_view = [(self.env.ref('sale.view_order_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = sale_orders.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_view_sale_confirm_orders(self):
        """
        This method will used for view of sale orders which running and not done or cancel are on this recurring order
        :return: dict: action
        """
        action = self.env["ir.actions.actions"]._for_xml_id(
            "sale.action_orders")
        if self._context.get('default_confirmed_sale_order', False):
            action['domain'] = [('recurring_order_id', '=', self.id), ('state', '=', 'sale'),
                                ('picking_ids.state', '!=', 'done')]
        else:
            action['domain'] = [('recurring_order_id', '=', self.id)]
        return action


class RecurringOrderLine(models.Model):
    _name = 'recurring.order.line'

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the Recurring order line.
        """
        for line in self:
            for line in self:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(price, line.recurring_order_id.currency_id, line.product_uom_qty,
                                                product=line.product_id, partner=line.recurring_order_id.partner_shipping_id)
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
                if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                        'account.group_account_manager'):
                    line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    recurring_order_id = fields.Many2one('recurring.order', string='Recurring Ref', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)

    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    discount = fields.Float('Discount')
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    product_id = fields.Many2one('product.product', string='Product', domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
            change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    state = fields.Selection(
            related='recurring_order_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')
    currency_id = fields.Many2one(related='company_id.currency_id', depends=['company_id.currency_id'], store=True, string='Currency', readonly=True)

    @api.onchange('product_id')
    @api.constrains('product_id')
    def product_id_change(self):
        for rec in self:
            if rec.product_id:
                rec.price_unit = rec.product_id.list_price
                rec.product_uom = rec.product_id.uom_id.id
                rec.name = rec.product_id.name

    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        # awa: don't know if it's still the case since we need the "product_no_variant_attribute_value_ids" field now
        # to be able to compute the full price

        if self.recurring_order_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.recurring_order_id.pricelist_id.id, uom=self.product_uom.id).price
        product_context = dict(self.env.context, partner_id=self.recurring_order_id.partner_id.id, date=self.recurring_order_id.start_date, uom=self.product_uom.id)

        final_price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(product or self.product_id, self.product_uom_qty or 1.0, self.recurring_order_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.recurring_order_id.pricelist_id.id)
        if currency != self.recurring_order_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.recurring_order_id.pricelist_id.currency_id,
                self.recurring_order_id.company_id or self.env.company, self.recurring_order_id.date_order or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)
