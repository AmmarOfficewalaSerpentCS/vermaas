# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductAttribute(models.Model):

    _inherit = "product.attribute"

    is_height_width = fields.Boolean(string="Is Height/Width")
    is_qty = fields.Boolean(string="Is Quantity")
