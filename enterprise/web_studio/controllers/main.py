# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree
from StringIO import StringIO
from odoo import http, _
from odoo.http import content_disposition, request
from odoo.exceptions import UserError, AccessError
from odoo.addons.web_studio.controllers import export


class WebStudioController(http.Controller):

    @http.route('/web_studio/init', type='json', auth='user')
    def studio_init(self):
        return {
            'dbuuid': request.env['ir.config_parameter'].get_param('database.uuid'),
            'multi_lang': bool(request.env['res.lang'].search_count([('code', '!=', 'en_US')])),
        }

    @http.route('/web_studio/chatter_allowed', type='json', auth='user')
    def is_chatter_allowed(self, model):
        """ Returns True iff a chatter can be activated on the model's form views, i.e. if
            - it is a custom model (since we can make it inherit from mail.thread), or
            - it already inherits from mail.thread.
        """
        Model = request.env[model]
        return Model._custom or isinstance(Model, type(request.env['mail.thread']))

    @http.route('/web_studio/get_studio_action', type='json', auth='user')
    def get_studio_action(self, action_name, model, view_id=None, view_type=None):
        view_type = 'tree' if view_type == 'list' else view_type  # list is stored as tree in db
        model = request.env['ir.model'].search([('model', '=', model)], limit=1)

        action = None
        if hasattr(self, '_get_studio_action_' + action_name):
            action = getattr(self, '_get_studio_action_' + action_name)(model, view_id=view_id, view_type=view_type)

        return action

    def _get_studio_action_acl(self, model, **kwargs):
        return {
            'name': _('Access Control Lists'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.model.access',
            'views': [[False, 'list'], [False, 'form']],
            'target': 'current',
            'domain': [],
            'context': {'search_default_model_id': model.id},
            'help': """ <p class="oe_view_nocontent_create">
                Click to add a new access control list.
            </p>
            """,
        }

    def _get_studio_action_automations(self, model, **kwargs):
        return {
            'name': _('Automated Actions'),
            'type': 'ir.actions.act_window',
            'res_model': 'base.action.rule',
            'views': [[False, 'list'], [False, 'form']],
            'target': 'current',
            'domain': [],
            'context': {'search_default_model_id': model.id},
            'help': """ <p class="oe_view_nocontent_create">
                Click to add a new automated action.
            </p>
            """,
        }

    def _get_studio_action_filters(self, model, **kwargs):
        return {
            'name': _('Search Filters'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.filters',
            'views': [[False, 'list'], [False, 'form']],
            'target': 'current',
            'domain': [],
            'context': {'search_default_model_id': model.model},  # model_id is a Selection on ir.filters
            'help': """ <p class="oe_view_nocontent_create">
                Click to add a new filter.
            </p>
            """,
        }

    def _get_studio_action_reports(self, model, **kwargs):
        return {
            'name': _('Reports'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.actions.report.xml',
            'views': [[False, 'kanban'], [False, 'form']],
            'target': 'current',
            'domain': [],
            'context': {'search_default_model': model.model},
            'help': """ <p class="oe_view_nocontent">
                There is no report available.
            </p>
            """,
        }

    def _get_studio_action_translations(self, model, **kwargs):
        """ Open a view for translating the field(s) of the record (model, id). """
        domain = ['|', ('name', '=', model.model), ('name', 'ilike', model.model + ',')]

        # search view + its inheritancies
        views = request.env['ir.ui.view'].search([('model', '=', model.model)])
        domain = ['|', '&', ('name', '=', 'ir.ui.view,arch_db'), ('res_id', 'in', views.ids)] + domain

        def make_domain(fld, rec):
            name = "%s,%s" % (fld.model_name, fld.name)
            return ['&', ('res_id', '=', rec.id), ('name', '=', name)]

        def insert_missing(fld, rec):
            if not fld.translate:
                return []

            if fld.related:
                try:
                    # traverse related fields up to their data source
                    while fld.related:
                        rec, fld = fld.traverse_related(rec)
                    if rec:
                        return ['|'] + domain + make_domain(fld, rec)
                except AccessError:
                    return []

            assert fld.translate and rec._name == fld.model_name
            request.env['ir.translation'].insert_missing(fld, rec)
            return []

        # insert missing translations of views
        for view in views:
            for name, fld in view._fields.items():
                domain += insert_missing(fld, view)

        # insert missing translations of model, and extend domain for related fields
        record = request.env[model.model].search([], limit=1)
        if record:
            for name, fld in record._fields.items():
                domain += insert_missing(fld, record)

        action = {
            'name': _('Translate view'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.translation',
            'view_mode': 'tree',
            'views': [[request.env.ref('base.view_translation_dialog_tree').id, 'list']],
            'target': 'current',
            'domain': domain,
        }

        return action

    @http.route('/web_studio/create_new_menu', type='json', auth='user')
    def create_new_menu(self, name, model_id, is_app=False, parent_id=None, icon=None):
        """ Create a new menu @name, linked to a new action associated to the model_id
            @param is_app: if True, create an extra menu (app, without parent)
            @param parent_id: the parent of the new menu.
                To be set if is_app is False.
            @param icon: the icon of the new app, like [icon, icon_color, background_color].
                To be set if is_app is True.
        """
        # create the action
        model = request.env['ir.model'].browse(model_id)
        new_action = request.env['ir.actions.act_window'].create({
            'name': name,
            'res_model': model.model,
            'help': """
                <p>
                    This is your new action ; by default, it contains a list view and a form view.
                </p>
                <p>
                    You can start customizing these screens by clicking on the Studio icon on the
                    top right corner (you can also customize this help message there).
                </p>
            """,
        })
        action_ref = 'ir.actions.act_window,' + str(new_action.id)

        if is_app:
            # create the menus (app menu + first submenu)
            new_context = dict(request.context)
            new_context.update({'ir.ui.menu.full_list': True})  # allows to create a menu without action
            new_menu = request.env['ir.ui.menu'].with_context(new_context).create({
                'name': name,
                'web_icon': ','.join(icon),
                'child_id': [(0, 0, {
                    'name': name,
                    'action': action_ref,
                })]
            })
        else:
            # create the submenu
            new_menu = request.env['ir.ui.menu'].create({
                'name': name,
                'action': action_ref,
                'parent_id': parent_id,
            })

        return {
            'menu_id': new_menu.id,
            'action_id': new_action.id,
        }

    @http.route('/web_studio/edit_action', type='json', auth='user')
    def edit_action(self, action_type, action_id, args):

        action_id = request.env[action_type].browse(action_id)
        if action_id:
            if 'groups_id' in args:
                args['groups_id'] = [(6, 0, args['groups_id'])]

            if 'view_mode' in args:
                args['view_mode'] = args['view_mode'].replace('list', 'tree')  # list is stored as tree in db

                # Check that each views in view_mode exists or try to get default
                view_ids = request.env['ir.ui.view'].search([('model', '=', action_id.res_model)])
                view_types = [view_id.type for view_id in view_ids]
                for view_type in args['view_mode'].split(','):
                    if view_type not in view_types:
                        try:
                            request.env[action_id.res_model].fields_view_get(view_type=view_type)
                        except UserError as e:
                            return e.name

                # As view_id and view_ids have precedence on view_mode, we need to correctly set them
                if action_id.view_id or action_id.view_ids:
                    view_modes = args['view_mode'].split(',')

                    # add new view_mode
                    missing_view_modes = [x for x in view_modes if x not in [y.view_mode for y in action_id.view_ids]]
                    for view_mode in missing_view_modes:
                        vals = {
                            'act_window_id': action_id.id,
                            'view_mode': view_mode,
                        }
                        if action_id.view_id and action_id.view_id.type == view_mode:
                            # reuse the same view_id in the corresponding view_ids record
                            vals['view_id'] = action_id.view_id.id

                        request.env['ir.actions.act_window.view'].create(vals)

                    for view_id in action_id.view_ids:
                        if view_id.view_mode in view_modes:
                            # resequence according to new view_modes
                            view_id.sequence = view_modes.index(view_id.view_mode)
                        else:
                            # remove old view_mode
                            view_id.unlink()

            action_id.write(args)

        return True

    @http.route('/web_studio/set_another_view', type='json', auth='user')
    def set_another_view(self, action_id, view_mode, view_id):

        action_id = request.env['ir.actions.act_window'].browse(action_id)
        window_view = request.env['ir.actions.act_window.view'].search([('view_mode', '=', view_mode), ('act_window_id', '=', action_id.id)])
        if not window_view:
            window_view = request.env['ir.actions.act_window.view'].create({'view_mode': view_mode, 'act_window_id': action_id.id})

        window_view.view_id = view_id

        return True

    def _get_studio_view(self, view):
        return request.env['ir.ui.view'].search([('inherit_id', '=', view.id), ('name', 'ilike', '%studio%customization%')], limit=1)

    @http.route('/web_studio/get_studio_view_arch', type='json', auth='user')
    def get_studio_view_arch(self, model, view_type, view_id=False):
        view_type = 'tree' if view_type == 'list' else view_type  # list is stored as tree in db

        if not view_id:
            # TOFIX: it's possibly not the used view ; see fields_get_view
            # try to find the lowest priority matching ir.ui.view
            view_id = request.env['ir.ui.view'].default_view(request.env[model]._name, view_type)
        # We have to create a view with the default view if we want to customize it.
        view = self._get_or_create_default_view(model, view_type, view_id)
        studio_view = self._get_studio_view(view)

        return {
            'studio_view_id': studio_view and studio_view.id or False,
            'studio_view_arch': studio_view and studio_view.arch_db or "<data/>",
        }

    @http.route('/web_studio/edit_view', type='json', auth='user')
    def edit_view(self, view_id, studio_view_arch, operations=None):
        view = request.env['ir.ui.view'].browse(view_id)
        studio_view = self._get_studio_view(view)

        parser = etree.XMLParser(remove_blank_text=True)
        arch = etree.parse(StringIO(studio_view_arch), parser).getroot()

        for op in operations:
            # Call the right operation handler
            if 'node' in op:
                op['node'] = self._preprocess_attrs(op['node'])
            getattr(self, '_operation_%s' % (op['type']))(arch, op, view.model)

        # Save or create changes into studio view, identifiable by xmlid
        # Example for view id 42 of model crm.lead: web-studio_crm.lead-42
        # TODO: if len(arch) == 0, delete the view
        new_arch = etree.tostring(arch, encoding='utf-8', pretty_print=True)
        if studio_view:
            studio_view.arch_db = new_arch
        else:
            # We have to play with priorities. Consider the following:
            # View Base: <field name="x"/><field name="y"/>
            # View Standard inherits Base: <field name="x" position="after"><field name="z"/></field>
            # View Custo inherits Base: <field name="x" position="after"><field name="x2"/></field>
            # We want x,x2,z,y, because that's what we did in studio, but the order of xpath
            # resolution is sequence,name, not sequence,id. Because "Custo" < "Standard", it
            # would first resolve in x,x2,y, then resolve "Standard" with x,z,x2,y as result.
            studio_view = request.env['ir.ui.view'].create({
                'type': view.type,
                'model': view.model,
                'inherit_id': view.id,
                'mode': 'extension',
                'priority': 99,
                'arch': new_arch,
                'name': "Odoo Studio: %s customization" % (view.name),
            })

        fields_view = request.env[view.model].with_context({'studio': True}).fields_view_get(view.id, view.type)

        return fields_view

    @http.route('/web_studio/edit_view_arch', type='json', auth='user')
    def edit_view_arch(self, view_id, view_arch):
        view = request.env['ir.ui.view'].browse(view_id)

        if view:
            view.write({'arch': view_arch})

            if view.model:
                try:
                    fields_view = request.env[view.model].with_context({'studio': True}).fields_view_get(view.id, view.type)
                    return fields_view
                except Exception:
                    return False

    @http.route('/web_studio/export', type='http', auth='user')
    def export(self, token):
        """ Exports a zip file containing the 'studio_customization' module
            gathering all customizations done with Studio (customizations of
            existing apps and freshly created apps).
        """
        studio_module = request.env['ir.module.module'].get_studio_module()
        data = request.env['ir.model.data'].search([('studio', '=', True)])
        content = export.generate_archive(studio_module, data)

        return request.make_response(content, headers=[
            ('Content-Disposition', content_disposition('customizations.zip')),
            ('Content-Type', 'application/zip'),
            ('Content-Length', len(content)),
        ], cookies={'fileToken': token})

    def _preprocess_attrs(self, node):
        # The js can't give us the field name, it only has the field id
        if node['tag'] == 'field' and 'id' in node['attrs']:
            node['attrs']['name'] = request.env['ir.model.fields'].browse(node['attrs'].pop('id')).name
        return node

    def _get_or_create_default_view(self, model, view_type, view_id=False):
        View = request.env['ir.ui.view']
        # If we have no view_id to inherit from, it's because we are adding
        # fields to the default view of a new model. We will materialize the
        # default view as a true view so we can keep using our xpath mechanism.
        if view_id:
            view = View.browse(view_id)
        else:
            arch = request.env[model].fields_view_get(view_id, view_type)['arch']
            view = View.create({
                'type': view_type,
                'model': model,
                'arch': arch,
                'name': "Default %s view for %s" % (view_type, model),
            })
        return view

    def _node_to_expr(self, node):
        if not node.get('attrs') and node.get('xpath_info'):
            # Format of expr is /form/tag1[]/tag2[]/[...]/tag[]
            expr = ''.join(['/%s[%s]' % (parent['tag'], parent['indice']) for parent in node.get('xpath_info')])
        else:
            # Format of expr is //tag[@attr1_name=attr1_value][@attr2_name=attr2_value][...]
            expr = '//' + node['tag'] + ''.join(['[@%s=\'%s\']' % (k, v) for k, v in node.get('attrs', {}).items()])
            # Avoid matching nodes in sub views.
            # Example with field as node:
            # A field should be defined only once in a view but in some cases,
            # a view can be composed by some other views where a field with
            # the same name may exist.
            # Here, we want to generate xpath based on the nodes in the parent view only.
            expr = expr + '[not(ancestor::field)]'

        # Special case when we have <label/><div/> instead of <field>
        # TODO: This is very naive, couldn't the js detect such a situation and
        #       tell us to anchor the xpath on another element ?
        if node['tag'] == 'label':
            expr = expr + '/following-sibling::div'

        return expr

    # Create a new xpath node based on an operation
    # TODO: rename it in master
    def _get_xpath_node(self, arch, operation):
        expr = self._node_to_expr(operation['target'])
        position = operation['position']

        return etree.SubElement(arch, 'xpath', {
            'expr': expr,
            'position': position
        })

    def _operation_remove(self, arch, operation, model=None):
        expr = self._node_to_expr(operation['target'])

        # We have to create a brand new xpath to remove this field from the view.
        # TODO: Sometimes, we have to delete more stuff than just a single tag !
        etree.SubElement(arch, 'xpath', {
            'expr': expr,
            'position': 'replace'
        })

    def _operation_add(self, arch, operation, model):
        node = operation['node']
        xpath_node = self._get_xpath_node(arch, operation)

        # Create the actual node inside the xpath. It needs to be the first
        # child of the xpath to respect the order in which they were added.
        xml_node = etree.Element(node['tag'], node.get('attrs'))
        if node['tag'] == 'notebook':
            # FIXME take the same randomString as parent
            name = 'studio_page_' + node['attrs']['name'].split('_')[2]
            xml_node_page = etree.Element('page', {'string': 'New Page', 'name': name})
            xml_node.insert(0, xml_node_page)
        elif node['tag'] == 'group':
            xml_node_page_right = etree.Element('group', {'string': 'Right Title', 'name': node['attrs']['name'] + '_right'})
            xml_node_page_left = etree.Element('group', {'string': 'Left Title', 'name': node['attrs']['name'] + '_left'})
            xml_node.insert(0, xml_node_page_right)
            xml_node.insert(0, xml_node_page_left)
        elif node['tag'] == 'button':
            # To create a stat button, we need
            #   - a many2one field (1) that points to this model
            #   - a field (2) that counts the number of records associated with the current record
            #   - an action to jump in (3) with the many2one field (1) as domain/context
            #
            # (1) [button_field] the many2one field
            # (2) [button_count_field] is a non-stored computed field (to always have the good value in the stat button, if access rights)
            # (3) [button_action] an act_window action to jump in the related model
            button_field = request.env['ir.model.fields'].browse(node['field'])
            button_count_field, button_action = self._get_or_create_fields_for_button(model, button_field, node['string'])

            # the XML looks like <button> <field/> </button : a element `field` needs to be inserted inside the button
            xml_node_field = etree.Element('field', {'widget': 'statinfo', 'name': button_count_field.name, 'string': node['string'] or button_count_field.field_description})
            xml_node.insert(0, xml_node_field)

            xml_node.attrib['type'] = 'action'
            xml_node.attrib['name'] = str(button_action.id)
        else:
            xml_node.text = node.get('text')
        xpath_node.insert(0, xml_node)

    def _get_or_create_fields_for_button(self, model, field, button_name):
        """ Returns the button_count_field and the button_action link to a stat button.
            @param field: a many2one field
        """

        if field.ttype != 'many2one' or field.relation != model:
            raise UserError(_('The related field of a button has to be a many2one to %s.' % model))

        model = request.env['ir.model'].search([('model', '=', model)], limit=1)

        # There is a counter on the button ; as the related field is a many2one, we need
        # to create a new computed field that counts the number of records in the one2many
        button_count_field_name = 'x_%s__%s_count' % (field.name, field.model.replace('.', '_'))[0:63]
        button_count_field = request.env['ir.model.fields'].search([('name', '=', button_count_field_name), ('model_id', '=', model.id)])
        if not button_count_field:
            compute_function = """
                    results = self.env['%(model)s'].read_group([('%(field)s', 'in', self.ids)], '%(field)s', '%(field)s')
                    dic = {}
                    for x in results: dic[x['%(field)s'][0]] = x['%(field)s_count']
                    for record in self: record['%(count_field)s'] = dic.get(record.id, 0)
                """ % {
                    'model': field.model,
                    'field': field.name,
                    'count_field': button_count_field_name,
                }
            button_count_field = request.env['ir.model.fields'].create({
                'name': button_count_field_name,
                'field_description': '%s count' % field.field_description,
                'model': model.model,
                'model_id': model.id,
                'ttype': 'integer',
                'store': False,
                'compute': compute_function.replace('    ', ''),  # remove indentation for safe_eval
            })

        # The action could already exist but we don't want to recreate one each time
        button_action_domain = "[('%s', '=', active_id)]" % (field.name)
        button_action_context = "{'search_default_%s': active_id,'default_%s': active_id}" % (field.name, field.name)
        button_action = request.env['ir.actions.act_window'].search([
            ('name', '=', button_name), ('res_model', '=', field.model),
            ('domain', '=', button_action_domain), ('context', '=', button_action_context),
        ])
        if not button_action:
            # Link the button with an associated act_window
            button_action = request.env['ir.actions.act_window'].create({
                'name': button_name,
                'res_model': field.model,
                'view_mode': 'tree,form',
                'view_type': 'form',
                'domain': button_action_domain,
                'context': button_action_context,
            })

        return button_count_field, button_action

    def _operation_move(self, arch, operation, model=None):
        self._operation_remove(arch, dict(operation, target=operation['node']))
        self._operation_add(arch, operation)

    # Create or update node for each attribute
    def _operation_attributes(self, arch, operation, model=None):
        ir_model_data = request.env['ir.model.data']
        new_attrs = operation['new_attrs']

        if (new_attrs.get('groups')):
            eval_attr = []
            for many2many_value in new_attrs['groups']:
                group_xmlid = ir_model_data.search([
                    ('model', '=', 'res.groups'),
                    ('res_id', '=', many2many_value)])
                eval_attr.append(group_xmlid.complete_name)
            eval_attr = ",".join(eval_attr)
            new_attrs['groups'] = eval_attr
        else:
            # TOFIX
            new_attrs['groups'] = ''

        xpath_node = self._get_xpath_node(arch, operation)

        for key, new_attr in new_attrs.iteritems():
            xml_node = xpath_node.find('attribute[@name="%s"]' % (key))
            if xml_node is None:
                xml_node = etree.Element('attribute', {'name': key})
                xml_node.text = new_attr
                xpath_node.insert(0, xml_node)
            else:
                xml_node.text = new_attr

    def _operation_buttonbox(self, arch, operation, model=None):
        studio_view_arch = arch  # The actual arch is the studio view arch
        # Get the arch of the form view with inherited views applied
        arch = request.env[model].fields_view_get(view_type='form')['arch']
        parser = etree.XMLParser(remove_blank_text=True)
        arch = etree.parse(StringIO(arch), parser).getroot()

        # Create xpath to put the buttonbox as the first child of the sheet
        if arch.find('sheet'):
            sheet_node = arch.find('sheet')
            if list(sheet_node): # Check if children exists
                xpath_node = etree.SubElement(studio_view_arch, 'xpath', {
                    'expr': '//sheet/*[1]',
                    'position': 'before'
                })
            else:
                xpath_node = etree.SubElement(studio_view_arch, 'xpath', {
                    'expr': '//sheet',
                    'position': 'inside'
                })
            # Create and insert the buttonbox node inside the xpath node
            buttonbox_node = etree.Element('div', {'name': 'button_box', 'class': 'oe_button_box'})
            xpath_node.append(buttonbox_node)

    def _operation_chatter(self, arch, operation, model=None):
        def _get_remove_field_op(arch, field_name):
            return {
                'type': 'remove',
                'target': {
                    'tag': 'field',
                    'attrs': {
                        'name': field_name,
                    },
                }
            }

        if not self.is_chatter_allowed(operation['model']):
            # Chatter can only be activated form models that (can) inherit from mail.thread
            return

        # From this point, the model is either a custom model or inherits from mail.thread
        model = request.env['ir.model'].search([('model', '=', operation['model'])])
        if model.state == 'manual' and not model.mail_thread:
            # Activate mail.thread inheritance on the custom model
            model.write({'mail_thread': True})

        # Remove message_ids and message_follower_ids if already defined in form view
        if operation['remove_message_ids']:
            self._operation_remove(arch, _get_remove_field_op(arch, 'message_ids'))
        if operation['remove_follower_ids']:
            self._operation_remove(arch, _get_remove_field_op(arch, 'message_follower_ids'))

        xpath_node = etree.SubElement(arch, 'xpath', {
            'expr': '//sheet',
            'position': 'after',
        })
        chatter_node = etree.Element('div', {'class': 'oe_chatter'})
        thread_node = etree.Element('field', {'name': 'message_ids', 'widget': 'mail_thread'})
        follower_node = etree.Element('field', {'name': 'message_follower_ids', 'widget': 'mail_followers'})
        chatter_node.append(follower_node)
        chatter_node.append(thread_node)
        xpath_node.append(chatter_node)
