import logging
from venv import logger
import requests
from odoo import models, fields, api # type: ignore
from odoo.addons.http_routing.models.ir_http import slug
from odoo.http import request
from datetime import datetime

class FacebookPage(models.Model):
    _name = 'marketing.product'
    _description = 'Integrate Facebook to marketing product'

    product_id = fields.Many2one('product.template', string='Product', required=True)

    account_ids = fields.Many2many('manager.account', string='Accounts', required=True)
    page_ids = fields.Many2many('facebook.page', string='Pages', required=True)

    message = fields.Text(string='Post Message')

    schedule_post = fields.Datetime(string='Schedule Post', required=True)
    remind_time = fields.Datetime(string='Remind Time', required=True)
   
    post_ids = fields.One2many('marketing.post', 'marketing_product_id', string='Posts')
    comment = fields.Text(string='Comment')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('failed', 'Failed')
    ], string='Status', default='draft', compute='_compute_state', store=True)

    @api.depends('post_ids.state')
    def _compute_state(self):
        for record in self:
            post_states = set(record.post_ids.mapped('state'))
            if not post_states:
                record.state = 'draft'
            elif post_states == {'posted'}:
                record.state = 'posted'
            elif 'failed' in post_states:
                record.state = 'failed'
            else:
                record.state = 'draft'

    @api.onchange('account_ids')
    def _onchange_account_ids(self):
        self.page_ids = False
        if self.account_ids:
            return {'domain': {'page_ids': [('account_id', 'in', self.account_ids.ids)]}}
        else:
            return {'domain': {'page_ids': []}}

    
    def post_product_to_facebook(self):
        for record in self:
            for page in record.page_ids:
                product = record.product_id
                message = record.message or f"Check out our new product: {product.name}"

                url = f"https://graph.facebook.com/{page.page_id}/feed"
                params = {
                    'message': message,
                    'access_token': page.access_token
                }
                logging.info(params)

                try:
                    response = requests.post(url, data=params)
                    response.raise_for_status()
                    data = response.json()
                    self.env['marketing.post'].create({
                        'marketing_product_id': record.id,
                        'page_id': page.id,
                        'post_id': data.get('id'),
                        'post_url': f"https://www.facebook.com/{data.get('id')}",
                        'state': 'posted'
                    })
                    # Thêm comment chứa URL của product
                    try:
                        comment_content = f"{request.httprequest.host_url}shop/{slug(product)}"
                        comment_response = requests.post(
                            f'https://graph.facebook.com/{post_id}/comments',
                            data={
                                'message': comment_content,
                                'access_token': page.access_token
                            }
                        )
                        comment_response.raise_for_status()
                        logging.info(f"Successfully added comment with blog URL to post")

                    except requests.exceptions.RequestException as e:
                        logging.error(f"Failed to post to page : {e}")

                except requests.exceptions.RequestException as e:
                    self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                        'title': 'Error',
                        'message': f"Failed to post to Facebook page {page.name}: {str(e)}",
                        'type': 'danger',
                    })
                

    def post_comment_to_facebook(self):
        for record in self:
            comment_content = record.comment

            for page in record.page:
                page_id = page.page_id
                access_token = page.access_token

                # Lọc các bài post chỉ thuộc về trang hiện tại
                page_post_lines = record.facebook_post_line.filtered(lambda line: line.post_id.startswith(page_id))

                for post_line in page_post_lines:
                    post_id = post_line.post_id

                    # _logger.info(f"Posting comment to Facebook post '{post_id}' on page '{page_id}' using access token '{access_token}'")

                    try:
                        response = requests.post(
                            f'https://graph.facebook.com/{post_id}/comments',
                            data={
                                'message': comment_content,
                                'access_token': access_token
                            }
                        )
                        response.raise_for_status()
                        logger.info(f"Successfully posted comment to post '{post_id}' on page '{page_id}'")
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Failed to post comment to post '{post_id}' on page '{page_id}': {e}")

