odoo.define('web.new_utils', function () {
"use strict";

function traverse_records(data, f) {
    if (data.is_record) {
        f(data);
    } else {
        for (var i = 0; i < data.data.length; i++) {
            traverse_records(data.data[i], f);
        }
    }
}

return {
    traverse_records: traverse_records,
};

});