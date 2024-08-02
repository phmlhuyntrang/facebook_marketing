import logging
import requests
from odoo import models, fields, api
from odoo.addons.http_routing.models.ir_http import slug
from odoo.http import request
from datetime import datetime

class FacebookPage(models.Model):
    _name = 'marketing.product'
    _description = 'Integrate Facebook to marketing product'

    # account_id = fields.Many2one('manager.account', string='Account', required=True)
    # page_id = fields.Many2one('facebook.page', string='Page', required=True)

    account_ids = fields.Many2many('manager.account', string='Accounts', required=True)
    page_ids = fields.Many2many('facebook.page', string='Pages', required=True)

    product_id = fields.Many2one('product.template', string='Product', required=True)
    message = fields.Text(string='Post Message')

    schedule_post = fields.Datetime(string='Schedule Post', required=True)
    remind_time = fields.Datetime(string='Remind Time', required=True)
   
    post_id = fields.Char('Post ID')
    post_url = fields.Char('Post URL')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('failed', 'Failed')
    ], string='Status', default='draft')

    @api.onchange('account_id')
    def _onchange_account_id(self):
        self.page_id = False
        return {'domain': {'page_id': [('account_id', '=', self.account_id.id)]}}
    
    def post_to_facebook(self):
        for record in self:
            page = record.page_id
            product = record.product_id
            message = record.message or f"Check out our new product: {product.name}"

            url = f"https://graph.facebook.com/{page.page_id}/feed"
            params = {
                'message': message,
                # 'link':  f"{request.httprequest.host_url}shop/{slug(product)}",
                # 'link':  "https://www.facebook.com/photo?fbid=122097784766425348&set=a.122097761138425348",
                # 'link': f"http://yourodoowebsite.com/shop/product/{product.id}",
                'access_token': page.access_token
            }
            logging.info(params)

            try:
                response = requests.post(url, data=params)
                response.raise_for_status()
                data = response.json()
                record.write({
                    'post_id': data.get('id'),
                    'post_url': f"https://www.facebook.com/{data.get('id')}",
                    'state': 'posted'
                })
            except requests.exceptions.RequestException as e:
                record.write({'state': 'failed'})
                self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                    'title': 'Error',
                    'message': f"Failed to post to Facebook: {str(e)}",
                    'type': 'danger',
                })