# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import requests
import logging

_logger = logging.getLogger(__name__)

QUERY_DOCUMENT = {
    'urls': {
        'dni': 'https://api.apis.net.pe/v1/dni?numero={vat}',
        'ruc': 'https://api.apis.net.pe/v1/ruc?numero={vat}'
    }
}


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ####### CONSULTA DNI #########
    related_identification = fields.Char(related='l10n_latam_identification_type_id.l10n_pe_vat_code', store=True)
    lastname_1 = fields.Char('Apellidos paterno')
    lastname_2 = fields.Char('Apellidos materno')
    names = fields.Char('Nombres')

    @api.onchange('vat', 'l10n_latam_identification_type_id')
    def onchange_identification(self):
        if self.l10n_latam_identification_type_id and self.vat:
            try:
                if self.l10n_latam_identification_type_id.l10n_pe_vat_code == '1':
                    self.verify_dni()
                elif self.l10n_latam_identification_type_id.l10n_pe_vat_code == '6':
                    self.verify_ruc()
            except Exception as ex:
                _logger.error('Ha ocurrido un error {}'.format(ex))

    @api.model
    def default_get(self, fields):
        res = super(ResPartner, self).default_get(fields)
        res['name'] = 'Nombre'
        res['names'] = '-'
        res['lastname_1'] = '-'
        res['lastname_2'] = '-'
        res['street'] = '-'
        return res

    def verify_dni(self):
        # parameters = self.env['sale.main.parameter'].verify_query_parameters()
        if not self.vat:
            raise UserError("Debe seleccionar un DNI")
        url = QUERY_DOCUMENT['urls']['dni'].format(vat=self.vat)
        token = self.env['ir.config_parameter'].sudo().get_param('sunat.query.token')
        headers = {'Authorization': f'Bearer {token}'}
        result = requests.get(url, verify=False, headers=headers)
        if result.status_code == 200:
            result_json = result.json()
            self.update({
                'name': result_json['nombre'].strip().upper(),
                'company_type': 'person'
            })
        else:
            raise ValidationError(f'Ha ocurrido un error al consultar DNI: {result.text}')

    ruc_state = fields.Char(string='RUC Estado')
    ruc_condition = fields.Char(string=u'RUC Condición')

    def verify_ruc(self):
        token = self.env['ir.config_parameter'].sudo().get_param('sunat.query.token')
        headers = {'Authorization': f'Bearer {token}'}
        district_obj = self.env['l10n_pe.res.city.district']
        for record in self:
            if self.l10n_latam_identification_type_id.l10n_pe_vat_code == '6':
                url = QUERY_DOCUMENT['urls']['ruc'].format(vat=record.vat)
                result = requests.get(url, headers=headers)
                if result.status_code == 200:
                    result_json = result.json()
                    district = district_obj.search([('name', '=ilike', result_json['distrito']), ('city_id.name', '=ilike', result_json['provincia'])], limit=1)
                    if not district.exists():
                        district = district_obj.search([('code', '=', result_json['ubigeo'])])
                    record.update({
                        'name': result_json['nombre'],
                        'street': result_json['direccion'].strip(),
                        'country_id': self.env.ref('base.pe').id,
                        'state_id': district.city_id.state_id.id,
                        'city_id': district.city_id.id,
                        'l10n_pe_district': district.id,
                        'ruc_state': result_json['estado'],
                        'ruc_condition': result_json['condicion'],
                        'zip': result_json['ubigeo'],
                        'company_type': 'company'
                    })
                else:
                    raise ValidationError(f'Ha ocurrido un error al consultar RUC: {result.text}')
