# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo.tests

@odoo.tests.common.at_install(False)
@odoo.tests.common.post_install(True)
class TestUi(odoo.tests.HttpCase):
    def test_ui(self):
        self.phantom_js("/", "odoo.__DEBUG__.services['web.Tour'].run('account_followup_reports_widgets_2', 'test')", "odoo.__DEBUG__.services['web.Tour'].tours.account_followup_reports_widgets_2", login='admin')