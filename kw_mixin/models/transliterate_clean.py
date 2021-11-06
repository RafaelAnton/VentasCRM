import logging
import re

from odoo import models, api

_logger = logging.getLogger(__name__)


def transliterate(name):
    if not isinstance(name, str):
        return name
    symbols = (
        'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ',
        'abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA')
    tr = {ord(a): ord(b) for a, b in zip(*symbols)}
    return name.translate(tr)


def transliterate_visual(name):
    if not isinstance(name, str):
        return name
    symbols = (
        'авекмнорстухАВЕКМНОРСТУХ',
        'abekmhopctyxABEKMHOPCTYX')
    tr = {ord(a): ord(b) for a, b in zip(*symbols)}
    return name.translate(tr)


class CleanUpMixin(models.AbstractModel):
    _name = 'kw.clean.up.mixin'
    _description = 'Clean up Mixin'

    @staticmethod
    def transliterate_visual(name):
        return transliterate_visual(name)

    @staticmethod
    def transliterate(name):
        return transliterate(name)

    @api.model
    def kw_cleanup_string(self, val):
        try:
            val = ''.join(i for i in val if (i.isdigit() or i.isalpha()))
        except Exception as e:
            _logger.debug('String "%s" has error %s', val, e)
            return ''
        return val

    @staticmethod
    def kw_clean_model_name(name):
        if not isinstance(name, str):
            return name
        name = transliterate_visual(name.upper())
        sym = '1234567890_-qwertyuiopasdfghjklzxcvbnm.'.upper()
        name = ''.join([x if x in sym else '' for x in name])
        return name

    @staticmethod
    def kw_clean_alpha_digit(name):
        if not isinstance(name, str):
            return name
        name = transliterate_visual(name.upper())
        sym = '1234567890qwertyuiopasdfghjklzxcvbnm'.upper()
        name = ''.join([x if x in sym else '' for x in name])
        return name

    @staticmethod
    def kw_clean_alpha_only(name):
        if not isinstance(name, str):
            return name
        name = transliterate_visual(name.upper())
        sym = 'qwertyuiopasdfghjklzxcvbnm'.upper()
        name = ''.join([x if x in sym else '' for x in name])
        return name

    @staticmethod
    def kw_clean_digit_only(phone):
        if not isinstance(phone, str):
            return phone
        sym = '1234567890'
        phone = ''.join([x if x in sym else '' for x in phone])
        return phone

    @staticmethod
    def kw_clean_index_model_name(name):
        if not isinstance(name, str):
            return name
        return CleanUpMixin.lg_clean_alpha_digit(name).replace('LG', '')

    @staticmethod
    def kw_clean_remove_html_tags(raw_html):
        expr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        return re.sub(expr, '', raw_html)
