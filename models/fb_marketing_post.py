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
            # Assuming 'name', 'content', 'author', and 'date_published' are fields in 'blog.post'
            blog_name = record.blog.name
            blog_content = record.blog.content
            blog_author = record.blog.author_id.name  # Assuming 'author_id' is a Many2one field to 'res.partner'

            # Format the content to post on Facebook
            post_content = (
                f"Blog Title: {blog_name}\n"
                f"Content: {blog_content}\n"
                f"Author: {blog_author}\n"
            )

            for page in record.page:
                page_id = page.page_id
                access_token = page.access_token

                # Logic to post the blog to Facebook
                _logger.info(f"Posting blog '{blog_name}' (ID: {record.blog.id}) to Facebook page '{page_id}' using access token '{access_token}'")
                
                try:
                    response = requests.post(
                        f'https://graph.facebook.com/{page_id}/feed',
                        data={
                            'message': post_content,
                            'access_token': access_token
                        }
                    )
                    response.raise_for_status()  # Raise an exception for HTTP errors
                    _logger.info(f"Successfully posted to page '{page_id}'")
                except requests.exceptions.RequestException as e:
                    _logger.error(f"Failed to post to page '{page_id}': {e}")