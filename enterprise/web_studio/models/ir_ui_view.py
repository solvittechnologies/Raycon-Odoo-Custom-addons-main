# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree
from lxml.builder import E
from odoo import models
import json
import uuid


class View(models.Model):
    _name = 'ir.ui.view'
    _inherit = ['studio.mixin', 'ir.ui.view']

    def _apply_group(self, model, node, modifiers, fields):
        # apply_group only returns the view groups ids.
        # As we need also need their name and display in Studio to edit these groups
        # (many2many widget), they have been added to node (only in Studio).
        if self._context.get('studio'):
            if node.get('groups'):
                studio_groups = []
                for xml_id in node.attrib['groups'].split(','):
                    group = self.env['ir.model.data'].xmlid_to_object(xml_id)
                    if group:
                        studio_groups.append({
                            "id": group.id,
                            "name": group.name,
                            "display_name": group.display_name
                        })
                node.attrib['studio_groups'] = json.dumps(studio_groups)

        return super(View, self)._apply_group(model, node, modifiers, fields)

    def create_simplified_form_view(self, res_model):
        model = self.env[res_model]
        rec_name = model._rec_name_fallback()
        field = E.field(name=rec_name, required='1')
        group_1 = E.group(field, name=str(uuid.uuid4())[:6], string='Left Title')
        group_2 = E.group(name=str(uuid.uuid4())[:6], string='Right Title')
        group = E.group(group_1, group_2, name=str(uuid.uuid4())[:6])
        form = E.form(E.sheet(group, string=model._description))
        arch = etree.tostring(form, encoding='utf-8')

        self.create({
            'type': 'form',
            'model': res_model,
            'arch': arch,
            'name': "Default %s view for %s" % ('form', res_model),
        })

    # Returns "true" if the view_id is the id of the studio view.
    def _is_studio_view(self):
        return self.xml_id.startswith('studio_customization')

    # Based on inherit_branding of ir_ui_view
    # This will add recursively the groups ids on the spec node.
    def _groups_branding(self, specs_tree, view_id):
        groups_id = self.browse(view_id).groups_id
        if groups_id:
            attr_value = ','.join(map(str, groups_id.ids))
            for node in specs_tree.iter(tag=etree.Element):
                node.set('studio-view-group-ids', attr_value)

    # Used for studio views only.
    # This studio view specification will not always be available.
    # So, we add the groups name to find out when they will be available.
    # This information will be used in Studio to inform the user.
    def _set_groups_info(self, node, group_ids):
        groups = self.env['res.groups'].browse(map(int, group_ids.split(',')))
        view_group_names = ','.join(groups.mapped('name'))
        for child in node.iter(tag=etree.Element):
            child.set('studio-view-group-names', view_group_names)
            child.set('studio-view-group-ids', group_ids)

    # Used for studio views only.
    # Check if the hook node depends of groups.
    def _check_parent_groups(self, source, spec):
        node = self.locate_node(source, spec)
        if node is not None and node.get('studio-view-group-ids'):
            # Propogate group info for all children
            self._set_groups_info(spec, node.get('studio-view-group-ids'))

    # Used for studio views only.
    # Apply spec by spec studio view.
    def _apply_studio_specs(self, source, specs_tree, studio_view_id):
        for spec in specs_tree.iterchildren(tag=etree.Element):
            if self._context.get('studio'):
                # Detect xpath base on a field added by a view with groups
                self._check_parent_groups(source, spec)
                # Here, we don't want to catch the exception.
                # This mechanism doesn't save the view if something goes wrong.
                source = super(View, self).apply_inheritance_specs(source, spec, studio_view_id)
            else:
                # Avoid traceback if studio view and skip xpath when studio mode is off
                try:
                    source = super(View, self).apply_inheritance_specs(source, spec, studio_view_id)
                except ValueError:
                    # 'locate_node' already log this error.
                    pass
        return source

    def apply_inheritance_specs(self, source, specs_tree, inherit_id):
        # Add branding for groups if studio mode is on
        if self._context.get('studio'):
            self._groups_branding(specs_tree, inherit_id)

        # If this is studio view, we want to apply it spec by spec
        if self.browse(inherit_id)._is_studio_view():
            return self._apply_studio_specs(source, specs_tree, inherit_id)
        else:
            return super(View, self).apply_inheritance_specs(source, specs_tree, inherit_id)

    def locate_node(self, arch, spec):
        # Remove branding added by '_groups_branding'
        spec.attrib.pop("studio-view-group-ids", None)
        return super(View, self).locate_node(arch, spec)
