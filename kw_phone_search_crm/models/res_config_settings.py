from odoo import models


class LeadResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def kw_crm_lead_phone_format_contacts(self):
        for obj in self.env['crm.lead'].search([]):
            obj.onchange_phone()
