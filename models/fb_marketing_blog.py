import logging
import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class MarketingBlog(models.Model):
    _name = 'marketing.blog'
    _description = 'Marketing Blog'

    blog = fields.Many2one('blog.post', string='Blog', required=True)

    account_ids = fields.Many2many('manager.account', string='Account', required=True)
    page_ids = fields.Many2many('facebook.page', string='Page', required=True)
    
    message = fields.Text(string='Post Message', required=True)
    schedule_post = fields.Datetime(string='Schedule Post', required=True)
    remind_time = fields.Datetime(string='Remind Time', required=True)
   
    post_ids = fields.One2many('marketing.post', 'marketing_blog_id', string='Posts')
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

    def post_blog_to_facebook(self):
        for record in self:
            blog_name = record.blog.name
            message = record.message
            blog_author = record.blog.author_id.name
            blog_url = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/blog/{record.blog.blog_id.id}/post/{record.blog.id}"

            post_content = (
                f"{message}\n"
                f"Blog: {blog_name}\n"
                f"Author: {blog_author}\n"
            )

            for page in record.page_ids:
                page_id = page.page_id
                access_token = page.access_token

                # _logger.info(f"Posting blog '{blog_name}' (ID: {record.blog.id}) to Facebook page '{page_id}' using access token '{access_token}'")

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

                    self.env['marketing.post'].create({
                        'marketing_blog_id': record.id,
                        'post_id': post_id,
                        'post_url': post_url,
                        'page_id': page.id,
                        'state': 'posted'

                    })

                    # _logger.info(f"Successfully posted to page '{page_id}' with post ID '{post_id}'")

                    # Thêm comment chứa URL của bài blog
                    # comment_content = f"{blog_url}"
                    comment_content = '@followers'
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


