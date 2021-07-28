from odoo import models, fields, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def import_sale_order_line(self):
        pass
