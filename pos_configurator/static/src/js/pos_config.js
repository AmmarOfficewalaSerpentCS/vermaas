odoo.define('pos_configurator.pos_configurator',function(require){
"use strict";
    
    const models = require('point_of_sale.models');
    const ProductConfiguratorPopup = require('point_of_sale.ProductConfiguratorPopup').ProductConfiguratorPopup;
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');

    models.load_fields("product.attribute",['is_height_width']);


    models.load_models({
        model: 'product.template.attribute.value',
        fields: ['product_attribute_value_id', 'attribute_id', 'attribute_line_id', 'price_extra'],
        condition: function (self) { return self.config.product_configurator; },
        domain: function(self, tmp){ return [['attribute_id', 'in', _.keys(tmp.product_attributes_by_id).map(parseFloat)]]; },
        loaded: function(self, ptavs, tmp) {
            self.attributes_by_ptal_id = {};
            _.map(ptavs, function (ptav) {
                if (!self.attributes_by_ptal_id[ptav.attribute_line_id[0]]){
                    self.attributes_by_ptal_id[ptav.attribute_line_id[0]] = {
                        id: ptav.attribute_line_id[0],
                        name: tmp.product_attributes_by_id[ptav.attribute_id[0]].name,
                        display_type: tmp.product_attributes_by_id[ptav.attribute_id[0]].display_type,
                        values: [],
                        is_height_width : tmp.product_attributes_by_id[ptav.attribute_id[0]].is_height_width
                    };
                }
                self.attributes_by_ptal_id[ptav.attribute_line_id[0]].values.push({
                    id: ptav.product_attribute_value_id[0],
                    name: tmp.pav_by_id[ptav.product_attribute_value_id[0]].name,
                    is_custom: tmp.pav_by_id[ptav.product_attribute_value_id[0]].is_custom,
                    html_color: tmp.pav_by_id[ptav.product_attribute_value_id[0]].html_color,
                    price_extra: ptav.price_extra,
                });
            });
        }
    })
    
    const PosProductConfiguratorPopup = (ProductConfiguratorPopup) =>
        class extends ProductConfiguratorPopup {
            
            getPayload() {
                const rec = super.getPayload();
                let order = this.env.pos.get_order();
                let qty = 1;
                order.custom_qty = 0;
                this.env.attribute_components.forEach((attribute_component) => {
                    let value = attribute_component.state.custom_value;
                    if (attribute_component.attribute.is_height_width){
                        qty = qty * parseFloat(value);
                    }
                });
                order.custom_qty = qty
                return rec
            }
    };

    const PosProductScreen = (ProductScreen) =>
        class extends ProductScreen  {
            async _getAddProductOptions(product) { 
                let rec = await super._getAddProductOptions(product);
                let order = this.env.pos.get_order();
                if (order.custom_qty){
                    rec.quantity = order.custom_qty
                }
                return rec
            }
        };
    Registries.Component.extend(ProductConfiguratorPopup, PosProductConfiguratorPopup);
    Registries.Component.extend(ProductScreen, PosProductScreen);

    return {
        ProductConfiguratorPopup,
        ProductScreen  
    };

});