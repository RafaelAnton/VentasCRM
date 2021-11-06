import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResPartnerPhoneFormat(models.Model):
    _name = 'crm.lead'
    _inherit = ['kw.phone.number.mixin', 'kw.clean.up.mixin', 'crm.lead', ]

    kw_crm_phone_number_name = fields.Char(
        compute='_compute_kw_phone_number_name', store=True, index=True,
        compute_sudo=True, )
    kw_crm_phone_number_display = fields.Char(
        compute='_compute_kw_phone_number_name', compute_sudo=True,
        search='_search_crm_kw_phone_number_display', )
    kw_customer_phone_number_name = fields.Char(
        compute='_compute_kw_partner_id_phone_number_name',
        search='_search_kw_partner_id_phone_number_name', )

    def _compute_kw_partner_id_phone_number_name(self):
        for obj in self:
            if obj.partner_id:
                obj.kw_customer_phone_number_name = \
                    obj.partner_id.kw_phone_number_name
            else:
                obj.kw_customer_phone_number_name = ''

    def _search_kw_partner_id_phone_number_name(self, operator, value):
        return [('partner_id.kw_phone_number_name', 'ilike',
                 self.kw_cleanup_string(value))]

    def _search_crm_kw_phone_number_display(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return [('kw_crm_phone_number_name', operator,
                 self.kw_cleanup_string(value))]

    def format_kw_phone_number_name(self):
        self.ensure_one()
        self.kw_crm_phone_number_name = '{}{}{}'.format(
            self.kw_cleanup_string(self.phone),
            self.kw_cleanup_string(self.name),
            self.kw_cleanup_string(self.email_from))

        name = '{}'.format(self.name)
        if self.phone:
            name += ' {}'.format(self.phone)
        if self.email_from:
            name += ' {}'.format(self.email_from)
        self.kw_crm_phone_number_display = name.strip()

    @api.depends('phone', 'name')
    def _compute_kw_phone_number_name(self):
        for obj in self:
            obj.format_kw_phone_number_name()

    @api.depends('phone')
    def onchange_phone(self):
        for obj in self:
            phone = self.kw_format_number(obj.phone)
            if phone:
                obj.phone = self.phone_format(phone)
            else:
                obj.phone = False
