#!/bin/bash

# Odoo extension creation tool, allow you to create an extension directory which can be imported directly in chrome

odoo_path=${1:-../../odoo}

[ -d extension/static/src/css ] || mkdir -p extension/static/src/css

lessc static/src/less/import.less > static/src/css/project_timesheet.css

cp -r static extension
cp views/timesheet.html extension
cp manifest.json extension

cp $odoo_path/addons/web/static/src/js/boot.js extension/static/src/js

[ -d extension/static/src/js/framework ] || mkdir extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/ajax.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/bus.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/class.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/data.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/data_model.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/local_storage.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/mixins.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/model.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/pyeval.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/qweb.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/registry.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/session.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/time.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/translation.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/utils.js extension/static/src/js/framework
cp $odoo_path/addons/web/static/src/js/framework/widget.js extension/static/src/js/framework

[ -d extension/static/src/js/services ] || mkdir extension/static/src/js/services
cp $odoo_path/addons/web/static/src/js/services/core.js extension/static/src/js/services
cp $odoo_path/addons/web/static/src/js/services/session.js extension/static/src/js/services

cp -r $odoo_path/addons/web/static/lib/fontawesome extension/static/lib
cp -r $odoo_path/addons/web/static/lib/jquery extension/static/lib
cp -r $odoo_path/addons/web/static/lib/jquery.ba-bbq extension/static/lib
cp -r $odoo_path/addons/web/static/lib/moment extension/static/lib
cp -r $odoo_path/addons/web/static/lib/nvd3 extension/static/lib
cp -r $odoo_path/addons/web/static/lib/py.js extension/static/lib
cp -r $odoo_path/addons/web/static/lib/qweb extension/static/lib
cp -r $odoo_path/addons/web/static/lib/underscore extension/static/lib
cp -r $odoo_path/addons/web/static/lib/underscore.string extension/static/lib

[ -d extension/static/lib/bootstrap/css ] || mkdir -p extension/static/lib/bootstrap/css
lessc $odoo_path/addons/web/static/lib/bootstrap/less/bootstrap.less > extension/static/lib/bootstrap/css/bootstrap.min.css

[ -d extension/static/lib/bootstrap/js ] || mkdir -p extension/static/lib/bootstrap/js
cp $odoo_path/addons/web/static/lib/bootstrap/js/modal.js extension/static/lib/bootstrap/js

echo "Extension created"
