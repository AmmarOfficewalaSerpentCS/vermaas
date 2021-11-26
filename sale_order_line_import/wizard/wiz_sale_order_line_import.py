"""TransientModel Model for the create wizard from branch."""

import base64
from xlrd import open_workbook
from odoo import _, fields, models
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

    def _bom_products(self, product_obj, data_list, total=0):
        componet_id = False
        componet_id = product_obj.search([("name", "=", str(data_list[7]))], limit=1)
        values = {
            "name": data_list[7],
            "sale_ok": True,
            "type": "product",
            "categ_id": self.env.ref("product.product_category_all").id,
        }
        if not componet_id:
            raise UserError(_("This Product %s not Found.", str(data_list[7])))
        else:
            componet_id.write(values)
        total += componet_id.standard_price * (data_list[8])
        return (
            tuple(
                (
                    0,
                    0,
                    {
                        "product_id": componet_id and componet_id.id or False,
                        "product_qty": data_list[8],
                    },
                )
            ),
            total,
        )

    def _operation_lines(self, data_list, work_center_id):
        return tuple(
            (
                0,
                0,
                {
                    "name": data_list[9],
                    "workcenter_id": work_center_id and work_center_id.id or False,
                    "worksheet_type": "google_slide",
                    "time_cycle_manual": data_list[11],
                },
            )
        )

    def import_line_file(self):
        self.ensure_one()
        self.check_xls_file()
        file_data = base64.decodebytes(self.import_file)
        wb = open_workbook(file_contents=file_data)
        product_obj = self.env["product.product"]
        work_center_obj = self.env["mrp.workcenter"]
        bom_obj = self.env["mrp.bom"]
        sale_order_line_obj = self.env["sale.order.line"]
        data_list = []
        bom_line_ids = [(5, 0)]
        operation_line_ids = [(5, 0)]
        sheet = wb.sheet_by_index(0)
        for line in (
            self.env["sale.order"].browse(self.env.context.get("active_id")).order_line
        ):
            if line.is_downpayment:
                continue
            old_product_id = line.product_id
            line.unlink()
            old_product_id.bom_ids.unlink()
            old_product_id.unlink()
        qty = 0
        total = 0
        description_sale = ''
        for rownum in range(sheet.nrows):
            work_center_id = False

            if rownum >= 1:
                data_list = sheet.row_values(rownum)
                new_data_list = []
                if sheet.nrows > rownum + 1:
                    new_data_list = sheet.row_values(rownum + 1)
                name = ""
                if data_list[0]:
                    description_sale = ''
                    
                    qty = data_list[1]
                    name += str(data_list[0])
                    product_id = product_obj.search([("name", "=", name)], limit=1)
                    manufacture_route = self.env.ref(
                        "mrp.route_warehouse0_manufacture", raise_if_not_found=False
                    ).id
                    description_sale = str(data_list[2])
                    mto_route = self.env.ref(
                        "stock.route_warehouse0_mto", raise_if_not_found=False
                    ).id
                    values = {
                        "name": name,
                        "sale_ok": True,
                        "categ_id": self.env.ref("product.product_category_all").id,
                        "produce_delay": data_list[4],
                        "type": "product",
                        "description_sale": str(data_list[2]),
                        "route_ids": [(6, 0, [manufacture_route, mto_route])],
                    }
                    product_id = product_obj.create(values)
                    if data_list[7]:
                        boms, total = self._bom_products(product_obj, data_list, total)
                        bom_line_ids.append(boms)
                    if data_list[10]:
                        work_center_id = work_center_obj.search(
                            [("name", "ilike", data_list[10])]
                        )
                        if not work_center_id:
                            raise UserError(_("Work center not found"))
                        operation_line_ids.append(
                            self._operation_lines(data_list, work_center_id)
                        )

                elif data_list[7]:
                    boms, total = self._bom_products(product_obj, data_list, total)
                    bom_line_ids.append(boms)
                    if data_list[10]:
                        work_center_id = work_center_obj.search(
                            [("name", "=", data_list[10])]
                        )
                        if not work_center_id:
                            raise UserError(_("Work center not found."))
                        operation_line_ids.append(
                            self._operation_lines(data_list, work_center_id)
                        )
                elif data_list[10]:
                    work_center_id = work_center_obj.search(
                        [("name", "=", data_list[10])]
                    )
                    if not work_center_id:
                        raise UserError(_("Work center not found."))
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
                    product_id.write({"list_price": total})
                    bom_line_ids = [(5, 0)]
                    operation_line_ids = [(5, 0)]
                    sale_order_line_obj.create(
                        {
                            "product_id": product_id.id,
                            "name": description_sale or product_id.display_name,
                            "product_uom_qty": qty and float(qty) or 0,
                            "order_id": self.env.context.get("active_id"),
                        }
                    )
                    total = 0
                    qty = 0
                # data_list[14] for Client Order Ref
                if len(data_list) > 14 and data_list[14]:
                    sale_rec = self.env[self.env.context.get("active_model")].browse(
                        self.env.context.get("active_id")
                    )
                    sale_rec.write({"client_order_ref": str(data_list[14])})
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
        product_id.write({"list_price": total})
        sale_order_line_obj.create(
            {
                "product_id": product_id.id,
                "name": description_sale or product_id.display_name,
                "product_uom_qty": qty and float(qty) or 0,
                "price_unit": product_id.lst_price,
                "order_id": self.env.context.get("active_id"),
            }
        )
