# See LICENSE file for full copyright and licensing details.

{
    # Module information
    "name": "Sale Order Line Import",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "category": "Sale",
    "sequence": "1",
    "summary": """Import Sale Order line, product and BOM.""",
    # Author
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "website": "http://www.serpentcs.com",
    # Dependencies
    "depends": ["sale_management", "mrp", "mrp_workorder"],
    # Views
    "data": [
        "security/ir.model.access.csv",
        "wizard/wiz_sale_order_line_import.xml",
        "views/sale_order.xml",
    ],
}
