import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)

PHONE_FEATURE_MODULES = [
    'kw_phone_search',
    'kw_phone_number_ua',
    'kw_phone_search_crm',
    'kw_phone_search_sale',
]


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Modules available
    module_kw_phone_search = fields.Boolean(
        string='Partner phone search')
    module_kw_phone_number_ua = fields.Boolean(
        string='Force Ukraine code')
    module_kw_phone_search_crm = fields.Boolean(
        string='CRM lead phone search')
    module_kw_phone_search_sale = fields.Boolean(
        string='Sale order phone search')

    # Modules available (helpers)
    need_install_kw_phone_search = fields.Boolean(
        compute='_compute_kw_phone_modules_can_install', )
    need_install_kw_phone_number_ua = fields.Boolean(
        compute='_compute_kw_phone_modules_can_install', )
    need_install_kw_phone_search_crm = fields.Boolean(
        compute='_compute_kw_phone_modules_can_install', )
    need_install_kw_phone_search_sale = fields.Boolean(
        compute='_compute_kw_phone_modules_can_install', )

    def _compute_kw_phone_modules_can_install(self):
        _logger.info('_compute_kw_phone_modules_can_install')
        available_module_names = self.env['ir.module.module'].search([
            ('name', 'in', PHONE_FEATURE_MODULES),
            ('state', '!=', 'uninstallable'), ]).mapped('name')
        _logger.info(available_module_names)
        _logger.info(self)
        for record in self:
            for module in PHONE_FEATURE_MODULES:
                setattr(record, 'need_install_%s' % module,
                        module not in available_module_names)
                # record['need_install_%s' % module] = \
                #     module not in available_module_names
