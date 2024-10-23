# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2008-2010 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                         Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright (c) 2012-2013, Grupo OPENTIA (<http://opentia.com>) Registered EU Trademark.
#                         Dpto. Consultoría <consultoria@opentia.es>
# Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                    Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>


{
    'name': 'Spain - Accounting (PGCE 2008) Reports',
    'version': '4.1',
    'author': 'Spanish Localization Team',
    'website': 'https://launchpad.net/openerp-spain',
    'category': 'Localization',
    'description': """
        Accounting reports for Spain
    """,
    'depends': [
        'l10n_es', 'account_reports',
    ],
    'data': [
        'data/account_financial_html_report_data.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
