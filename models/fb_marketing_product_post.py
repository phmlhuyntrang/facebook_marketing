import logging
from venv import logger
import requests
from odoo import models, fields, api # type: ignore
from odoo.addons.http_routing.models.ir_http import slug
from odoo.http import request
from datetime import datetime

class MarketingPost(models.Model):
    _name = 'marketing.product.post'
    _description = 'Marketing Post'

    marketing_product_id = fields.Many2one('marketing.product', string='Marketing Product', ondelete='cascade')

    account_id = fields.Many2one('manager.account', string='Account', required=True)
    page_id = fields.Many2one('facebook.page', string='Page', domain="[('account_id', '=', account_id)]")
   
    comment = fields.Text(string='Comment')
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

    def post_product_to_facebook(self):
        # for record in self:
        #     for page in record.page_ids:
        #         product = record.product_id
        #         message = record.message or f"Check out our new product: {product.name}"

        #         url = f"https://graph.facebook.com/{page.page_id}/feed"
        #         params = {
        #             'message': message,
        #             'access_token': page.access_token
        #         }
        #         logging.info(params)

        #         try:
        #             response = requests.post(url, data=params)
        #             response.raise_for_status()
        #             data = response.json()
        #             self.env['marketing.post'].create({
        #                 'marketing_product_id': record.id,
        #                 'page_id': page.id,
        #                 'post_id': data.get('id'),
        #                 'post_url': f"https://www.facebook.com/{data.get('id')}",
        #                 'state': 'posted'
        #             })
        #             # Thêm comment chứa URL của product
        #             try:
        #                 comment_content = f"{request.httprequest.host_url}shop/{slug(product)}"
        #                 comment_response = requests.post(
        #                     f'https://graph.facebook.com/{data.get("id")}/comments',
        #                     data={
        #                         'message': comment_content,
        #                         'access_token': page.access_token
        #                     }
        #                 )
        #                 comment_response.raise_for_status()
        #                 logging.info(f"Successfully added comment with blog URL to post")

        #             except requests.exceptions.RequestException as e:
        #                 logging.error(f"Failed to post to page : {e}")

        #         except requests.exceptions.RequestException as e:
        #             self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
        #                 'title': 'Error',
        #                 'message': f"Failed to post to Facebook page {page.name}: {str(e)}",
        #                 'type': 'danger',
        #             })
        return True
                

    def post_comment_to_facebook(self):
        # for record in self:
        #     comment_content = record.comment

        #     for page in record.page:
        #         page_id = page.page_id
        #         access_token = page.access_token

        #         # Lọc các bài post chỉ thuộc về trang hiện tại
        #         page_post_lines = record.facebook_post_line.filtered(lambda line: line.post_id.startswith(page_id))

        #         for post_line in page_post_lines:
        #             post_id = post_line.post_id

        #             # _logger.info(f"Posting comment to Facebook post '{post_id}' on page '{page_id}' using access token '{access_token}'")

        #             try:
        #                 response = requests.post(
        #                     f'https://graph.facebook.com/{post_id}/comments',
        #                     data={
        #                         'message': comment_content,
        #                         'access_token': access_token
        #                     }
        #                 )
        #                 response.raise_for_status()
        #                 logger.info(f"Successfully posted comment to post '{post_id}' on page '{page_id}'")
        #             except requests.exceptions.RequestException as e:
        #                 logger.error(f"Failed to post comment to post '{post_id}' on page '{page_id}': {e}")
        return True
