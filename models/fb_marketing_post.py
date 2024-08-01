from odoo import models, fields, api
import logging
import requests

_logger = logging.getLogger(__name__)

class MarketingPost(models.Model):
    _name = 'marketing.post'
    _description = 'Marketing Post'

    account = fields.Many2one('manager.account', string='Account', required=True)
    page = fields.Many2many('facebook.page', string='Page', required=True)
    blog = fields.Many2one('blog.post', string='Blog', required=True)

    def post_blog_to_facebook(self):
        for record in self:
            blog_content = record.blog.name  # Assuming 'name' contains the blog content
            blog_id = record.blog.id

            for page in record.page:
                page_id = page.page_id
                access_token = page.access_token

                # Logic to post the blog to Facebook
                _logger.info(f"Posting blog '{blog_content}' (ID: {blog_id}) to Facebook page '{page_id}' using access token '{access_token}'")
                
                # Example API call (this is just a placeholder and needs to be replaced with actual API call)
                response = requests.post(
                    f'https://graph.facebook.com/{page_id}/feed',
                    data={
                        'message': blog_content,
                        'access_token': access_token
                    }
                )
                if response.status_code == 200:
                    _logger.info(f"Successfully posted to page '{page_id}'")
                else:
                    _logger.error(f"Failed to post to page '{page_id}': {response.text}")