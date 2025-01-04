odoo.define('product_blueprint_manager.BlueprintEditor', function (require) {
    "use strict";

    const Widget = require('web.Widget');
    const FieldBinaryImage = require('web.basic_fields').FieldBinaryImage;

    const BlueprintEditor = Widget.extend({
        events: {
            'click img': '_onClick',
        },

        _onClick: function (event) {
            const img = event.target;
            const rect = img.getBoundingClientRect();
            const offsetX = event.clientX - rect.left;
            const offsetY = event.clientY - rect.top;

            const inputX = this.$el.find("input[name='position_x']");
            const inputY = this.$el.find("input[name='position_y']");

            inputX.val(offsetX).change();
            inputY.val(offsetY).change();
        },
    });

    return {
        BlueprintEditor,
    };
});
