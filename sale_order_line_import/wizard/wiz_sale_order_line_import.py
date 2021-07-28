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

    def _create_bom_products(self, product_obj, data_list):
        componet_id = False
        componet_id = product_obj.search([("name", "=", str(data_list[16]))], limit=1)
        values = {
            "name": data_list[16],
            "sale_ok": True,
            "type": "product",
            "categ_id": self.env.ref("product.product_category_all").id,
        }
        if not componet_id:
            componet_id = product_obj.create(values)
        else:
            componet_id.write(values)
        return tuple(
            (
                0,
                0,
                {
                    "product_id": componet_id and componet_id.id or False,
                    "product_qty": data_list[17],
                    # 'product_uom_id': uom_id and uom_id.id or False,
                },
            )
        )

    def _operation_lines(self, data_list, work_center_id):
        return tuple(
            (
                0,
                0,
                {
                    "name": data_list[22],
                    "workcenter_id": work_center_id and work_center_id.id or False,
                    "worksheet_type": "google_slide",
                    "time_cycle_manual": data_list[24],
                },
            )
        )

    def _set_product_type(self, product_type):
        if product_type == "Storable Product":
            type = "product"
        if product_type == "Consumable":
            type = "consu"
        if product_type == "Service":
            type = "service"
        return type

    def import_line_file(self):
        self.check_xls_file()
        file_data = base64.decodebytes(self.import_file)
        wb = open_workbook(file_contents=file_data)
        product_obj = self.env["product.product"]
        # product_category = self.env['product.category']
        work_center_obj = self.env["mrp.workcenter"]
        bom_obj = self.env["mrp.bom"]
        # uom_obj = self.env['uom.uom']
        route = self.env["stock.location.route"]
        sale_order_line_obj = self.env["sale.order.line"]
        data_list = []
        sale_line_id = False
        bom_line_ids = [(5, 0)]
        operation_line_ids = [(5, 0)]
        sheet = wb.sheet_by_index(0)
        for rownum in range(sheet.nrows):

            work_center_id = False
            if rownum >= 1:
                data_list = sheet.row_values(rownum)
                new_data_list = []
                if sheet.nrows > rownum + 1:
                    new_data_list = sheet.row_values(rownum + 1)
                name = ""
                # product_category_id = product_category.search(
                #     [('name', '=', data_list[4])], limit=1)
                # if not product_category_id:
                #     product_category_id = product_category.create({
                #         'name': str(data_list[5])
                #     })
                if data_list[4]:
                    name += str(data_list[4])
                    if data_list[0]:
                        sale_line_id = sale_order_line_obj.browse(
                            int(data_list[0])
                        ).exists()
                        if sale_line_id:
                            product_id = sale_line_id.product_id
                            product_id.write(
                                {
                                    "name": name,
                                    "categ_id": self.env.ref(
                                        "product.product_category_all"
                                    ).id,
                                    "produce_delay": data_list[8],
                                    "description_sale": str(data_list[6]),
                                }
                            )
                        else:
                            product_id = product_obj.search(
                                [("name", "=", name)], limit=1
                            )
                            route_list = []
                            for r in data_list[13].split(","):
                                route_list.append(route.search([("name", "=", r)]).id)
                            if not product_id:
                                values = {
                                    "name": name,
                                    "sale_ok": data_list[11],
                                    "purchase_ok": data_list[12],
                                    "type": self._set_product_type(data_list[10]),
                                    "categ_id": self.env.ref(
                                        "product.product_category_all"
                                    ).id,
                                    "produce_delay": data_list[8],
                                    "description_sale": str(data_list[6]),
                                    "route_ids": [
                                        (6, 0, list(filter(None, route_list)))
                                    ],
                                }
                                product_id = product_obj.create(values)
                            else:
                                product_id.write(
                                    {
                                        "name": name,
                                        "categ_id": self.env.ref(
                                            "product.product_category_all"
                                        ).id,
                                        "produce_delay": data_list[8],
                                        "description_sale": str(data_list[6]),
                                    }
                                )

                    else:
                        product_id = product_obj.search([("name", "=", name)], limit=1)
                        route_list = []
                        for r in data_list[13].split(","):
                            route_list.append(route.search([("name", "=", r)]).id)
                        if not product_id:
                            values = {
                                "name": name,
                                "sale_ok": data_list[11],
                                "purchase_ok": data_list[12],
                                "type": self._set_product_type(data_list[10]),
                                "categ_id": self.env.ref(
                                    "product.product_category_all"
                                ).id,
                                "produce_delay": data_list[8],
                                "description_sale": str(data_list[6]),
                                "route_ids": [(6, 0, list(filter(None, route_list)))],
                            }
                            product_id = product_obj.create(values)

                        else:
                            product_id.write(
                                {
                                    "name": name,
                                    "categ_id": self.env.ref(
                                        "product.product_category_all"
                                    ).id,
                                    "produce_delay": data_list[8],
                                    "description_sale": str(data_list[6]),
                                }
                            )
                    if data_list[16]:
                        bom_line_ids.append(
                            self._create_bom_products(product_obj, data_list)
                        )
                    if data_list[23]:

                        work_center_id = work_center_obj.search(
                            [("name", "=", data_list[23])]
                        )
                        if not work_center_id:
                            raise UserError(_("Work center not found."))
                        operation_line_ids.append(
                            self._operation_lines(data_list, work_center_id)
                        )

                elif data_list[16]:
                    bom_line_ids.append(
                        self._create_bom_products(product_obj, data_list)
                    )
                    if data_list[23]:
                        work_center_id = work_center_obj.search(
                            [("name", "=", data_list[23])]
                        )
                        if not work_center_id:
                            raise UserError(_("Work center not found."))
                        operation_line_ids.append(
                            self._operation_lines(data_list, work_center_id)
                        )
                elif data_list[23]:
                    work_center_id = work_center_obj.search(
                        [("name", "=", data_list[23])]
                    )
                    if not work_center_id:
                        raise UserError(_("Work center not found."))
                    operation_line_ids.append(
                        self._operation_lines(data_list, work_center_id)
                    )
                if new_data_list and new_data_list[4]:
                    if len(product_id.bom_ids.ids) == 1:
                        product_id.bom_ids.write(
                            {
                                "bom_line_ids": bom_line_ids,
                                "operation_ids": operation_line_ids,
                            }
                        )
                    else:
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
                    if not sale_line_id:
                        sale_order_line_obj.create(
                            {
                                "product_id": product_id.id,
                                "name": product_id.display_name,
                                "product_uom_qty": data_list[5] or 0,
                                "order_id": self.env.context.get("active_id"),
                            }
                        )
                    else:
                        sale_line_id.write({"product_uom_qty": data_list[5] or 0})
                    sale_line_id = False
        if len(product_id.bom_ids.ids) == 1:
            product_id.bom_ids.write(
                {"bom_line_ids": bom_line_ids, "operation_ids": operation_line_ids}
            )
        else:
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
        if not sale_line_id:
            sale_order_line_obj.create(
                {
                    "product_id": product_id.id,
                    "name": product_id.display_name,
                    "product_uom_qty": data_list[5] or 0,
                    "order_id": self.env.context.get("active_id"),
                }
            )
        else:
            sale_line_id.write({"product_uom_qty": data_list[5] or 0})
        sale_line_id = False
