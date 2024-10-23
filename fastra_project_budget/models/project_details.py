# -*- coding: utf-8 -*-

from odoo import models, fields

class ProjectDetails(models.Model):
    _name = 'project.details'

    name = fields.Char("Name")