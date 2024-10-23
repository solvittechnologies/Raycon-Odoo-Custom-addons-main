# -*- coding: utf-8 -*-
import requests
import json
import datetime
import logging

from odoo import models, api, fields
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

class PlaidProviderAccount(models.Model):
    _inherit = ['account.online.provider']

    provider_type = fields.Selection(selection_add=[('plaid', 'Plaid')])

    def _migrate_token(self):
        # Check in ir_config_parameter if already migrated
        ICP_obj = self.env['ir.config_parameter'].sudo()
        migrated = ICP_obj.get_param('plaid_migrated') or False
        if not migrated:
            # Need to be done in sudo to ensure that we migrate all records at the same time in multi company
            providerAccounts = self.sudo().search([('provider_type', '=', 'plaid')])
            AccountProvider = self.env['account.online.provider'].with_context(ignore_migrate=True)
            for providerAccount in providerAccounts:
                data = {'access_token_v1': providerAccount.provider_account_identifier}
                resp_json = AccountProvider.plaid_fetch('/item/access_token/update_version', {}, data)
                if (resp_json.get('access_token')):
                    providerAccount.provider_account_identifier = resp_json.get('access_token')
            ICP_obj.set_param('plaid_migrated', True)
            # Need to commit otherwise we'll have a concurrent transaction update that is caused by update_status
            # because update_status uses a separate cursor to save plaid messages on record in case of error.
            self.env.cr.commit()
        return True


    def _get_plaid_credentials(self):
        ICP_obj = self.env['ir.config_parameter'].sudo()
        login = ICP_obj.get_param('plaid_id') or self._cr.dbname
        secret = ICP_obj.get_param('plaid_secret') or ICP_obj.get_param('database.uuid')
        url = ICP_obj.get_param('plaid_service_url') or 'https://onlinesync.odoo.com/plaid/api/2'
        return {'login': login, 'secret': secret, 'url': url,}

    def check_plaid_error(self, resp):
        try:
            resp_json = resp.json()
            # Reply to /item/get may encapsulate the error in the error key
            if type(resp_json) == dict and resp_json.get('error', False):
                resp_json = resp_json.get('error')
            if type(resp_json) == dict and resp_json.get('error_code') and resp.status_code >= 400:
                message = _('There was en error with Plaid Services!') + '\n{message: %s,\nerror code: %s,\nerror type: %s,\nrequest id: %s}'
                message = message % (resp_json.get('display_message') or resp_json.get('error_message'), 
                    resp_json.get('error_code', ''), resp_json.get('error_type', ''), resp_json.get('request_id', ''))
                if self and self.id:
                    self._update_status('FAILED', resp_json)
                    self.log_message(message)
                raise UserError(message)
            elif resp.status_code in (400, 403):
                if self and self.id:
                    self._update_status('FAILED', {})
                    self.log_message(resp.text)
                raise UserError(resp.text)
            resp.raise_for_status()
        except (requests.HTTPError, ValueError):
            message = _('Get %s status code for call to %s. Content message: %s') % (resp.status_code, resp.url, resp.text)
            if self and self.id:
                self.log_message(message)
            raise UserError(message)

    @api.multi
    def plaid_fetch(self, url, params, data, type_request="POST"):
        credentials = self._get_plaid_credentials()
        if not self.env.context.get('ignore_migrate'):
            self._migrate_token()
        url = credentials['url'] + url
        try:
            data['client_id'] = credentials['login']
            data['secret'] = credentials['secret']
            if len(self.ids) and self.provider_account_identifier:
                data['access_token'] = self.provider_account_identifier
            # This is only intended to work with Odoo proxy, if user wants to use his own plaid account
            # replace the query by requests.post(url, json=data, timeout=60)
            resp = requests.post(url, data=json.dumps(data), timeout=60)
        except requests.exceptions.Timeout:
            raise UserError(_('Timeout: the server did not reply within 60s'))
        self.check_plaid_error(resp)
        resp_json = resp.json()
        if self and self.id:
            self._update_status('SUCCESS', resp_json)
        if resp_json.get('jsonrpc', '') == '2.0':
            return resp_json.get('result')
        return resp.json()

    @api.multi
    def get_institution(self, searchString):
        ret = super(PlaidProviderAccount, self).get_institution(searchString)
        resp_json = {}
        try:
            resp = requests.post(url='https://onlinesync.odoo.com/onlinesync/search/', data={'query': searchString, 'country': False, 'provider': json.dumps(['plaid'])}, timeout=60)
            resp_json = resp.json()
        except requests.exceptions.Timeout:
            raise UserError(_('Timeout: the server did not reply within 60s'))
        except ValueError:
            raise UserError(_('Server not reachable, please try again later'))
        # return json.dumps(resp_json)
        for inst in resp_json.get('match'):
            ret.append({
                'id': inst.get('institution_identifier'),
                'name': inst.get('name'),
                'status': 'Supported',
                'countryISOCode': '',
                'relevance': inst.get('relevance1'),
                'baseUrl': '/',
                'loginUrl': '/',
                'type_provider': 'plaid'
            })
        return sorted(ret, key=lambda p: p.get('relevance', 0))

    @api.multi
    def get_login_form(self, site_id, provider):
        if provider != 'plaid':
            return super(PlaidProviderAccount, self).get_login_form(site_id, provider)
        ctx = self.env.context.copy()
        ctx['method'] = 'add'
        return {
            'type': 'ir.actions.client',
            'tag': 'plaid_online_sync_widget',
            'target': 'new',
            'institution_id': site_id,
            'open_link': True,
            'public_key': self.plaid_fetch('/public_key', {}, {}).get('public_key'),
            'context': ctx,
        }

    def link_success(self, public_token, metadata):
        # convert public token to access_token and create a provider with accounts defined in metadata
        data = {'public_token': public_token}
        resp_json = self.plaid_fetch('/item/public_token/exchange', {}, data)
        item_vals = {
            'name': metadata.get('institution', {}).get('name', ''),
            'provider_type': 'plaid', 
            'provider_account_identifier': resp_json.get('access_token'),
            'provider_identifier': metadata.get('institution', {}).get('institution_id', ''),
            'status': 'SUCCESS',
            'status_code': 0
        }
        accounts_ids = [m.get('id') for m in metadata.get('accounts') if m.get('id')]
        # Call plaid to get balance on all selected accounts.
        data = {'access_token': resp_json.get('access_token'), 'options': {'account_ids': accounts_ids}}
        resp_json = self.plaid_fetch('/accounts/balance/get', {}, data)
        account_vals = []
        for acc in resp_json.get('accounts'):
            account_vals.append((0, 0, {
                'name': acc.get('name'),
                'account_number': acc.get('mask'),
                'online_identifier': acc.get('account_id'),
                'balance': acc.get('balances', {}).get('available', 0),
            }))
        item_vals['account_online_journal_ids'] = account_vals
        provider_account = self.create(item_vals)
        result = {'status': 'SUCCESS', 'added': provider_account.account_online_journal_ids, 'method': self.env.context.get('method')}
        if self.env.context.get('journal_id', False):
            result['journal_id'] = self.env.context.get('journal_id')
        
        return self.open_action('account_online_sync.action_account_online_wizard_form', len(result.get('added')))

    @api.multi
    def _update_status(self, status, resp_json=None):
        if not resp_json:
            resp_json = {}
        code = str(resp_json.get('error_code', 0))
        message = resp_json.get('display_message') or resp_json.get('error_message') or ''
        message += ' (' + resp_json.get('error_type', '') + ')'
        with self.pool.cursor() as cr:
            self = self.with_env(self.env(cr=cr)).write({
                'status': status, 
                'status_code': code, 
                'last_refresh': fields.Datetime.now(),
                'message': message,
                'action_required': True if status == 'FAILED' else False
            })

    @api.multi
    def update_status(self, status, code=None, message=None):
        return UserError('This method is deprecated')

    @api.multi
    def plaid_add_update_provider_account(self, values, site_id, name, mfa=False):
        return UserError('This method is deprecated')

    @api.multi
    def plaid_add_update_account(self, resp_json):
        return UserError('This method is deprecated')

    @api.multi
    def manual_sync(self):
        if self.provider_type != 'plaid':
            return super(PlaidProviderAccount, self).manual_sync()
        transactions = []
        for account in self.account_online_journal_ids:
            if account.journal_ids:
                tr = account.retrieve_transactions()
                transactions.append({'journal': account.journal_ids[0].name, 'count': tr})

        ctx = dict(self._context or {})
        ctx.update({'init_call': False, 'transactions': transactions})
        return {
            'type': 'ir.actions.client',
            'tag': 'plaid_online_sync_end_widget',
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def update_credentials(self):
        if self.provider_type != 'plaid':
            return super(PlaidProviderAccount, self).update_credentials()
        # Create public token and open link in update mode with that token
        resp_json = self.plaid_fetch('/item/public_token/create', {}, {})
        ret_action = self.get_login_form(self.provider_identifier, 'plaid')
        ret_action['public_token'] = resp_json.get('public_token')
        ret_action['account_online_provider_id'] = self.id
        ctx = self.env.context.copy()
        ctx['method'] = 'edit'
        ctx['journal_id'] = False
        return ret_action

    @api.model
    def cron_fetch_online_transactions(self):
        if self.provider_type != 'plaid':
            return super(PlaidProviderAccount, self).cron_fetch_online_transactions()
        self.manual_sync()

    @api.multi
    def unlink(self):
        for provider in self:
            if provider.provider_type == 'plaid':
                # call plaid to ask to remove item
                try:
                    ctx = self._context.copy()
                    ctx['no_post_message'] = True
                    provider.with_context(ctx).plaid_fetch('/item/remove', {}, {})
                except UserError:
                    # If call to fails, don't prevent user to delete record 
                    pass
        super(PlaidProviderAccount, self).unlink()

class PlaidAccount(models.Model):
    _inherit = 'account.online.journal'

    @api.multi
    def retrieve_transactions(self):
        if (self.account_online_provider_id.provider_type != 'plaid'):
            return super(PlaidAccount, self).retrieve_transactions()
        transactions = []
        offset = 0
        # transactions are paginated by 500 results so we need to loop to ensure we have every transactions
        while True:
            params = {
                'start_date': self.last_sync or fields.Date.today(),
                'end_date': fields.Date.today(),
                'options': {'account_ids': [self.online_identifier], 'count': 500, 'offset': offset},
            }
            resp_json = self.account_online_provider_id.plaid_fetch('/transactions/get', {}, params)
            # Update the balance
            for account in resp_json.get('accounts', []):
                if account.get('account_id', '') == self.online_identifier:
                    end_amount = account.get('balances', {}).get('current', 0)
            # Prepare the transaction
            for transaction in resp_json.get('transactions'):
                if transaction.get('pending') == False:
                    trans = {
                        'id': transaction.get('transaction_id'),
                        'date': transaction.get('date'),
                        'description': transaction.get('name'),
                        'amount': -1 * transaction.get('amount'), #https://plaid.com/docs/api/#transactions amount positive if purchase
                        'end_amount': end_amount,
                    }
                    if 'location' in transaction:
                        trans['location'] = transaction.get('location')
                    transactions.append(trans)
            if resp_json.get('total_transactions', 0) <= offset + 500:
                break
            else:
                offset += 500
        # Create the bank statement with the transactions
        return self.env['account.bank.statement'].online_sync_bank_statement(transactions, self.journal_ids[0])
