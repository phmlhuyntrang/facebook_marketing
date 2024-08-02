import logging
import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class MarketingPost(models.Model):
    _name = 'marketing.post'
    _description = 'Marketing Post'

    account = fields.Many2one('manager.account', string='Account', required=True)
    page = fields.Many2many('facebook.page', string='Page', required=True)
    blog = fields.Many2one('blog.post', string='Blog', required=True)
    facebook_post_line = fields.One2many('facebook.post.line', 'marketing_post_id', string='Facebook Post Lines')
    facebook_content = fields.Text(string='Facebook Content', required=True)
    comment = fields.Text(string='Comment')

    def post_blog_to_facebook(self):
        for record in self:
            blog_name = record.blog.name
            facebook_content = record.facebook_content
            blog_author = record.blog.author_id.name
            blog_url = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/blog/{record.blog.blog_id.id}/post/{record.blog.id}"

            post_content = (
                f"{facebook_content}\n"
                f"Blog: {blog_name}\n"
                f"Author: {blog_author}\n"
            )

            for page in record.page:
                page_id = page.page_id
                access_token = page.access_token

                _logger.info(f"Posting blog '{blog_name}' (ID: {record.blog.id}) to Facebook page '{page_id}' using access token '{access_token}'")

                try:
                    # Đăng bài viết
                    response = requests.post(
                        f'https://graph.facebook.com/{page_id}/feed',
                        data={
                            'message': post_content,
                            'access_token': access_token,
                        }
                    )
                    response.raise_for_status()
                    post_data = response.json()
                    post_id = post_data.get('id')
                    post_url = f"https://www.facebook.com/{post_id.replace('_', '/posts/')}"

                    self.env['facebook.post.line'].create({
                        'marketing_post_id': record.id,
                        'post_id': post_id,
                        'post_url': post_url,
                    })

                    _logger.info(f"Successfully posted to page '{page_id}' with post ID '{post_id}'")

                    # Thêm comment chứa URL của bài blog
                    comment_content = f"{blog_url}"
                    comment_response = requests.post(
                        f'https://graph.facebook.com/{post_id}/comments',
                        data={
                            'message': comment_content,
                            'access_token': access_token
                        }
                    )
                    comment_response.raise_for_status()
                    _logger.info(f"Successfully added comment with blog URL to post '{post_id}' on page '{page_id}'")

                except requests.exceptions.RequestException as e:
                    _logger.error(f"Failed to post to page '{page_id}' or add comment: {e}")

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

                    _logger.info(f"Posting comment to Facebook post '{post_id}' on page '{page_id}' using access token '{access_token}'")

                    try:
                        response = requests.post(
                            f'https://graph.facebook.com/{post_id}/comments',
                            data={
                                'message': comment_content,
                                'access_token': access_token
                            }
                        )
                        response.raise_for_status()
                        _logger.info(f"Successfully posted comment to post '{post_id}' on page '{page_id}'")
                    except requests.exceptions.RequestException as e:
                        _logger.error(f"Failed to post comment to post '{post_id}' on page '{page_id}': {e}")