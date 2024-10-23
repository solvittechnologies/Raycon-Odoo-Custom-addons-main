# -*- coding: utf-8 -*-

from odoo import models
from datetime import datetime
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

import logging
_logger = logging.getLogger(__name__)

class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        res = super(IrHttp, self).session_info()

        now = datetime.now()
        Config = self.env["ir.config_parameter"].sudo()
        database_expiration_date = Config.get_param("database_expiration_date", None)

        if database_expiration_date:
            database_expiration_date = datetime.strptime(database_expiration_date, DEFAULT_SERVER_DATETIME_FORMAT)
            delta = database_expiration_date - now

            try:
                database_expiration_warning_delay = int(Config.get_param("database_expiration_warning_delay", 7))
                if not database_expiration_warning_delay > 1:
                    raise ValueError("Value must be greater than 1")
            except ValueError as e:
                _logger.warning("Could not get expiration warning delay: %s. Using default: 7 days" % str(e))
                database_expiration_warning_delay = 7

            if now > database_expiration_date:
                res["database_block_message"] = "Your database is expired"
            elif delta.days == 30:
                res["database_expiration_message"] = "Your database will expire in 1 month"
                res["database_block_is_warning"] = True
            elif delta.days > database_expiration_warning_delay:
                pass
            elif delta.days > 1:
                res["database_expiration_message"] = "Your database will expire in {} days".format(delta.days)
                res["database_block_is_warning"] = True
            elif delta.days == 1:
                res["database_expiration_message"] = "Your database will expire tomorrow"
                res["database_block_is_warning"] = True
            elif delta.days == 0:
                res["database_expiration_message"] = "Your database will expire today"
                res["database_block_is_warning"] = True

        return res