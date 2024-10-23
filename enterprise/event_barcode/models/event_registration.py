# -*- coding: utf-8 -*-
import logging
import uuid

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    @api.model
    def _get_random_token(self):
        """Generate a 20 char long pseudo-random string of digits

        Used for barcode generation, UUID4 makes the chance of a collision
        (unicity constraint) highly unlikely.
        Using the int version is a longer string than hex but generates a more
        compact barcode when using digits only (Code128C instead of Code128A).
        Keep only the first 8 bytes as a 16 bytes barcode is not readable by all
        barcode scanners.
         """
        return str(int(uuid.uuid4().bytes[:8].encode('hex'), 16))

    barcode = fields.Char(default=_get_random_token, readonly=True, copy=False)

    _sql_constraints = [
        ('barcode_event_uniq', 'unique(barcode, event_id)', "Barcode should be unique per event")
    ]

    @api.model_cr_context
    def _init_column(self, column_name):
        """ to avoid generating a single default barcide when installing the module,
            we need to set the default row by row for this column """
        if column_name == "barcode":
            _logger.debug("Table '%s': setting default value of new column %s to unique values for each row",
                          self._table, column_name)
            self.env.cr.execute("SELECT id FROM %s WHERE barcode IS NULL" % self._table)
            registration_ids = self.env.cr.dictfetchall()
            query_list = [{'id': reg['id'], 'barcode': self._get_random_token()} for reg in registration_ids]
            query = 'UPDATE ' + self._table + ' SET barcode = %(barcode)s WHERE id = %(id)s;'
            self.env.cr._obj.executemany(query, query_list)
            self.env.cr.commit()

        else:
            super(EventRegistration, self)._init_column(column_name)
