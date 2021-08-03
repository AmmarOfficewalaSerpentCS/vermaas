"""TransientModel Model for the create wizard from branch."""

import base64
from xlrd import open_workbook
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WizBranchWarehouse(models.TransientModel):

    _name = "wiz.sale.order.line.import"
    _description = "Wizard Sale order Line Import"

    import_file = fields.Binary("Import File")
    file_name = fields.Char("File name")

    def check_xls_file(self):
        if self.import_file:
            filename = self.file_name.rsplit(".")
            if filename and filename[-1] != "xls" and filename[-1] != "xlsx":
                raise UserError(_("You can attach only excle file."))

    def _create_bom_products(self, product_obj, data_list, total=0, qty=1):
        componet_id = False
        new_product = False
        componet_id = product_obj.search(
            [("name", "=", str(data_list[12]))], limit=1)
        values = {
            "name": data_list[12],
            "sale_ok": True,
            "type": "product",
            "categ_id": self.env.ref("product.product_category_all").id,
        }
        if not componet_id:
            componet_id = product_obj.create(values)
            new_product = componet_id
        else:
            componet_id.write(values)
        total += (componet_id.lst_price * (data_list[13] / qty))
        return tuple(
            (
                0,
                0,
                {
                    "product_id": componet_id and componet_id.id or False,
                    "product_qty": data_list[13],
                },
            )
        ), new_product, total

    def _operation_lines(self, data_list, work_center_id):
        return tuple(
            (
                0,
                0,
                {
                    "name": data_list[18],
                    "workcenter_id": work_center_id and work_center_id.id or False,
                    "worksheet_type": "google_slide",
                    "time_cycle_manual": data_list[20],
                },
            )
        )

    def _set_product_type(self, product_type):
        type = ""
        if product_type.lower() == "storable product":
            type = "product"
        if product_type.lower() == "consumable":
            type = "consu"
        if product_type.lower() == "service":
            type = "service"
        return type

    def import_line_file(self):
        self.ensure_one()
        self.check_xls_file()
        file_data = base64.decodebytes(self.import_file)
        wb = open_workbook(file_contents=file_data)
        product_obj = self.env["product.product"]
        work_center_obj = self.env["mrp.workcenter"]
        bom_obj = self.env["mrp.bom"]
        route = self.env["stock.location.route"]
        sale_order_line_obj = self.env["sale.order.line"]
        bom_operation = self.env["mrp.routing.workcenter"]
        data_list = []
        bom_line_ids = [(5, 0)]
        operation_line_ids = [(5, 0)]
        sheet = wb.sheet_by_index(0)
        for line in self.env['sale.order'].browse(self.env.context.get("active_id")).order_line:
            old_product_id = line.product_id
            line.unlink()
            old_product_id.bom_ids.unlink()
            old_product_id.unlink()
        qty = 0
        bom_products_name = ""
        operation_names = ""
        total = 0
        for rownum in range(sheet.nrows):
            work_center_id = False

            if rownum >= 1:
                data_list = sheet.row_values(rownum)
                new_data_list = []
                if sheet.nrows > rownum + 1:
                    new_data_list = sheet.row_values(rownum + 1)
                name = ""
                if data_list[0]:
                    qty = data_list[1]
                    name += str(data_list[0])
                    product_id = product_obj.search(
                        [("name", "=", name)], limit=1)
                    route_list = []
                    for r in data_list[9].split(","):
                        route_id = route.search([("name", "=", r)])
                        if route_id:
                            route_list.append(route_id.id)
                    values = {
                        "name": name,
                        "sale_ok": data_list[7],
                        "purchase_ok": data_list[8],
                        "type": self._set_product_type(data_list[6]),
                        "categ_id": self.env.ref(
                            "product.product_category_all"
                        ).id,
                        "produce_delay": data_list[4],
                        "description_sale": str(data_list[2]),
                        "route_ids": [(6, 0, route_list)],


                    }
                    product_id = product_obj.create(values)
                    if data_list[12]:
                        boms, new_bom_product, total = self._create_bom_products(
                            product_obj, data_list, total, qty)
                        bom_line_ids.append(boms)
                        if new_bom_product:
                            bom_products_name += str(new_bom_product.name)
                    if data_list[18]:
                        work_center_id = work_center_obj.search(
                            [("name", "ilike", data_list[19])]
                        )
                        operation = bom_operation.search(
                            [("name", "ilike", data_list[18])])
                        if not work_center_id:
                            raise UserError(_("Work center not found.3"))
                        if not operation:
                            operation_names += str(data_list[18])
                        operation_line_ids.append(
                            self._operation_lines(data_list, work_center_id)
                        )

                elif data_list[12]:
                    boms, new_bom_product, total = self._create_bom_products(
                        product_obj, data_list, total, qty)
                    bom_line_ids.append(boms)
                    if new_bom_product:
                        bom_products_name += str(new_bom_product.name)
                    if data_list[18]:
                        work_center_id = work_center_obj.search(
                            [("name", "=", data_list[19])]
                        )
                        if not work_center_id:
                            raise UserError(_("Work center not found.1"))
                        operation = bom_operation.search(
                            [("name", "ilike", data_list[18])])
                        if not operation:
                            operation_names += str(data_list[18])
                        operation_line_ids.append(
                            self._operation_lines(data_list, work_center_id)
                        )
                elif data_list[18]:
                    work_center_id = work_center_obj.search(
                        [("name", "=", data_list[19])]
                    )
                    if not work_center_id:
                        raise UserError(_("Work center not found.2"))
                    operation = bom_operation.search(
                        [("name", "ilike", data_list[18])])
                    if not operation:
                        operation_names += str(data_list[18])
                    operation_line_ids.append(
                        self._operation_lines(data_list, work_center_id)
                    )
                if new_data_list and new_data_list[0]:
                    bom_id = bom_obj.create(
                        {
                            "product_tmpl_id": product_id
                            and product_id.product_tmpl_id.id
                            or False,
                            "product_id": product_id and product_id.id or False,
                            "bom_line_ids": bom_line_ids,
                            "operation_ids": operation_line_ids,
                        }
                    )
                    product_id.write({
                        'list_price' : total
                    })
                    bom_line_ids = [(5, 0)]
                    operation_line_ids = [(5, 0)]
                    sale_order_line_obj.create(
                        {
                            "product_id": product_id.id,
                            "name": product_id.display_name,
                            "product_uom_qty": qty and float(qty) or 0,
                            "order_id": self.env.context.get("active_id"),
                        }
                    )
                    total = 0
                    qty = 0
        bom_id = bom_obj.create(
            {
                "product_tmpl_id": product_id
                and product_id.product_tmpl_id.id
                or False,
                "product_id": product_id and product_id.id or False,
                "bom_line_ids": bom_line_ids,
                "operation_ids": operation_line_ids,
            }
        )
        bom_line_ids = [(5, 0)]
        operation_line_ids = [(5, 0)]
        product_id.write({
            'list_price' : total
        })
        sale_order_line_obj.create(
            {
                "product_id": product_id.id,
                "name": product_id.display_name,
                "product_uom_qty": qty and float(qty) or 0,
                "price_unit": product_id.lst_price,
                "order_id": self.env.context.get("active_id"),
            }
        )
        if bom_products_name:
            title = _("New Product Creation Succeeded!")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': title,
                    'message': bom_products_name,
                    'sticky': False,
                }
            }
        bom_products_name = False
