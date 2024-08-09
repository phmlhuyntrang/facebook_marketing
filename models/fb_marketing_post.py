# from odoo import models, fields, api
# from datetime import datetime, timedelta
# import base64
# import logging
# import requests

# _logger = logging.getLogger(__name__)

# class MarketingPost(models.Model):
#     _name = 'marketing.post'
#     _description = 'Marketing Post'

#     marketing_blog_id = fields.Many2one('marketing.blog', string='Marketing Blog')
#     marketing_product_id = fields.Many2one('marketing.product', string='Marketing Product', ondelete='cascade')

#     account_id = fields.Many2one('manager.account', string='Account', required=True)
#     page_id = fields.Many2one('facebook.page', string='Page', domain="[('account_id', '=', account_id)]")

#     schedule_post = fields.Datetime(string='Đặt lịch post bài')

#     comment = fields.Text(string='Comment')
#     comment_suggestion_id = fields.Many2one('marketing.comment', string='Comment Suggestion')
#     remind_time = fields.Selection([
#         ('1', '1 minute'),
#         ('2', '2 minutes'), 
#         ('3', '3 minutes'),
#         ('4', '4 minutes'),
#         ('5', '5 minutes'),
#         ('stop', 'Stop Auto Comment')
#     ], string='Remind Time', default='')
    
#     post_id = fields.Char('Post ID')
#     post_url = fields.Char('Post URL')
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('scheduled', 'Scheduled'),
#         ('posted', 'Posted'),
#         ('failed', 'Failed')
#     ], string='Status', default='draft')
#     last_auto_comment_time = fields.Datetime('Last Auto Comment Time')

#     @api.model
#     def run_auto_comment_cron(self):
#         _logger.info("Chạy cron job auto-comment")
#         self._auto_comment()
    
#     @api.onchange('account_id')
#     def _onchange_account_id(self):
#         self.page_id = False
#         return {'domain': {'page_id': [('account_id', '=', self.account_id.id)]}}

#     @api.onchange('comment_suggestion_id')
#     def _onchange_comment_suggestion_id(self):
#         if self.comment_suggestion_id:
#             self.comment = self.comment_suggestion_id.name

#     @api.onchange('schedule_post')
#     def _onchange_schedule_post(self):
#         for record in self:
#             if record.schedule_post:
#                 record.state = 'scheduled'
#                 _logger.info(f"Scheduled post with ID {record.id} at {record.schedule_post}")

#     def _post_scheduled_blogs(self):
#         current_time = datetime.now()
#         _logger.info(f"Checking for scheduled posts at {current_time}")
#         scheduled_posts = self.search([('schedule_post', '<=', current_time), ('state', '=', 'scheduled')])
#         _logger.info(f"Found {len(scheduled_posts)} scheduled posts to process")
#         for post in scheduled_posts:
#             _logger.info(f"Attempting to post blog with ID {post.id}")
#             post.post_blog_to_facebook()
#             if post.state == 'posted':
#                 _logger.info(f"Successfully posted blog with ID {post.id}")
#             else:
#                 _logger.error(f"Failed to post blog with ID {post.id}")

#     def post_blog_to_facebook(self):
#         for record in self:
#             blog = record.marketing_blog_id.blog
#             blog_title = record.marketing_blog_id.blog_title
#             blog_name = blog.name
#             blog_author = blog.author_id.name
#             # blog_url = record.marketing_blog_id.link
#             blog_image = record.marketing_blog_id.image
#             blog_url = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/blog/{record.marketing_blog_id.blog.blog_id.id}/post/{record.marketing_blog_id.id}"

#             post_content = (
#                 f"{blog_title}\n"
#                 f"Blog: {blog_name}\n"
#                 f"Author: {blog_author}\n"
#             )

#             if record.marketing_blog_id.include_link:
#                 post_content += f"\nTìm hiểu thêm: {blog_url}"
#                 _logger.info(f"Thong tin blog URL: {blog_url}")

#             _logger.info(f"Include link: {record.marketing_blog_id.include_link}")
#             try:
#                 data = {
#                     'message': post_content,
#                     'access_token': record.page_id.access_token,
#                 }
#                 files = {}
#                 if blog_image:
#                     image_data = base64.b64decode(blog_image)
#                     files['source'] = ('image.jpg', image_data, 'image/jpeg')

#                 _logger.debug(f"Posting to Facebook with data: {data} and files: {files}")

#                 response = requests.post(
#                     f'https://graph.facebook.com/{record.page_id.page_id}/photos',
#                     data=data,
#                     files=files
#                 )
#                 response.raise_for_status()
#                 post_data = response.json()
#                 record.post_id = post_data.get('id')
#                 record.post_url = f"https://www.facebook.com/{record.post_id.replace('_', '/posts/')}"
                
#                 comment_content = f"{blog_url}"
#                 comment_response = requests.post(
#                     f'https://graph.facebook.com/{record.post_id}/comments',
#                     data={
#                         'message': comment_content,
#                         'access_token': record.page_id.access_token
#                     }
#                 )
#                 comment_response.raise_for_status()
#                 _logger.info(f"Successfully added comment with blog URL to post '{record.post_id}' on page '{record.page_id.page_id}'")
#                 record.state = 'posted'

#             except requests.exceptions.RequestException as e:
#                 record.state = 'failed'
#                 _logger.error(f"Failed to post to page '{record.page_id.page_id}' or add comment: {e}")
#                 _logger.debug(f"Response content: {e.response.content if e.response else 'No response content'}")

#     def post_product_to_facebook(self):
#         for record in self:
#             product = record.marketing_product_id.product_id
#             message = record.marketing_product_id.product_name
#             product_url = record.marketing_product_id.product_url
#             image = record.marketing_product_id.product_image

#             post_content = message

#             # if record.marketing_blog_id.include_link:
#             #     post_content += f"\nTìm hiểu thêm: {blog_url}"

#             try:
#                 data = {
#                     'message': post_content,
#                     'access_token': record.page_id.access_token,
#                 }
#                 files = {}
#                 if image:
#                     image_data = base64.b64decode(image)
#                     files['source'] = ('image.jpg', image_data, 'image/jpeg')

#                 # _logger.debug(f"Posting to Facebook with data: {data} and files: {files}")

#                     response = requests.post(
#                         f'https://graph.facebook.com/{record.page_id.page_id}/photos',
#                         data=data,
#                         files=files
#                     )
#                 else:
#                     response = requests.post(
#                         f'https://graph.facebook.com/{record.page_id.page_id}/feed',
#                         data=data
#                     )
#                 if record.marketing_product_id.show_product_url:
#                     #  Thêm comment chứa URL của product
#                     try:
#                         comment_content = f"{product_url}"
#                         comment_response = requests.post(
#                             f'https://graph.facebook.com/{record.post_id}/comments',
#                             data={
#                                 'message': comment_content,
#                                 'access_token': record.page_id.access_token
#                             }
#                         )
#                         comment_response.raise_for_status()
#                         logging.info(f"Successfully added comment with blog URL to post")

#                     except requests.exceptions.RequestException as e:
#                         logging.error(f"Failed to post to page : {e}")

#                 response.raise_for_status()
#                 post_data = response.json()
#                 record.post_id = post_data.get('id')
#                 record.post_url = f"https://www.facebook.com/{record.post_id.replace('_', '/posts/')}"
                
#             except requests.exceptions.RequestException as e:
#                 record.state = 'failed'
#                 _logger.error(f"Failed to post to page '{record.page_id.page_id}' or add comment: {e}")
#                 _logger.debug(f"Response content: {e.response.content if e.response else 'No response content'}")
    
#     def _post_scheduled_product(self):
#         current_time = datetime.now()
#         _logger.info(f"Checking for scheduled posts at {current_time}")
#         scheduled_posts = self.search([('schedule_post', '<=', current_time), ('state', '=', 'scheduled')])
#         _logger.info(f"Found {len(scheduled_posts)} scheduled posts to process")
#         for post in scheduled_posts:
#             _logger.info(f"Attempting to post product with ID {post.id}")
#             post.post_product_to_facebook()
#             if post.state == 'posted':
#                 _logger.info(f"Successfully posted product with ID {post.id}")
#             else:
#                 _logger.error(f"Failed to post product with ID {post.id}")

#     def post_comment_to_facebook(self):
#         for record in self:
#             comment_content = record.comment

#             # Kiểm tra nếu comment rỗng hoặc chỉ chứa khoảng trắng thì không cho post comment lên page
#             if not comment_content or not comment_content.strip():
#                 _logger.warning(f"Comment is empty or only whitespace for post '{record.post_id}' on page '{record.page_id.page_id}', skipping.")
#                 continue

#             next_page = True
#             page_url = f'https://graph.facebook.com/{record.post_id}/comments'

#             while next_page:
#                 try:
#                     response = requests.post(
#                         page_url,
#                         data={
#                             'message': comment_content,
#                             'access_token': record.page_id.access_token
#                         }
#                     )
#                     response.raise_for_status()
#                     _logger.info(f"Successfully posted comment to post '{record.post_id}' on page '{record.page_id.page_id}'")

#                     # Kiểm tra xem có trang tiếp theo không
#                     response_data = response.json()
#                     next_page = 'paging' in response_data and 'next' in response_data['paging']
#                     if next_page:
#                         page_url = response_data['paging']['next']
#                     else:
#                         next_page = False

#                 except requests.exceptions.RequestException as e:
#                     _logger.error(f"Failed to post comment to post '{record.post_id}' on page '{record.page_id.page_id}': {e}")
#                     next_page = False

#     def _auto_comment(self):
#         current_time = datetime.now()
#         _logger.info(f"Chạy kiểm tra auto-comment lúc {current_time}")
#         posts_to_comment = self.search([
#             ('state', '=', 'posted'),
#             ('post_id', '!=', False),
#             '|', ('last_auto_comment_time', '=', False),
#             ('last_auto_comment_time', '<=', current_time - timedelta(minutes=1))
#         ])
        
#         _logger.info(f"Tìm thấy {len(posts_to_comment)} bài viết cần comment")

#         for post in posts_to_comment:
#             _logger.info(f"Kiểm tra bài viết ID {post.post_id} với thời gian nhắc nhở {post.remind_time} phút")
#             if post.remind_time != 'stop' and (not post.last_auto_comment_time or (current_time - post.last_auto_comment_time).total_seconds() / 60 >= int(post.remind_time)):
#                 _logger.info(f"Đang đăng auto-comment cho bài viết ID {post.post_id}")
#                 post.post_comment_to_facebook()
#                 post.last_auto_comment_time = current_time
#                 _logger.info(f"Thời gian auto-comment được cập nhật cho bài viết ID {post.post_id} là {post.last_auto_comment_time}")
#             elif post.remind_time == 'stop':
#                 _logger.info(f"Auto comment đã được tắt cho bài viết ID {post.post_id}")

#     def post_random_comment_to_facebook(self):
#         self.ensure_one()
#         comment_content = self.comment

#         if not comment_content or not comment_content.strip():
#             _logger.warning(f"Nội dung comment trống hoặc chỉ chứa khoảng trắng cho bài viết '{self.post_id}', bỏ qua.")
#             return

#         try:
#             response = requests.post(
#                 f'https://graph.facebook.com/{self.post_id}/comments',
#                 data={
#                     'message': comment_content,
#                     'access_token': self.page_id.access_token
#                 }
#             )
#             response.raise_for_status()
#             _logger.info(f"Đăng auto-comment thành công cho bài viết '{self.post_id}' trên trang '{self.page_id.page_id}' với nội dung: {comment_content}")
#         except requests.exceptions.RequestException as e:
#             _logger.error(f"Đăng auto-comment thất bại cho bài viết '{self.post_id}' trên trang '{self.page_id.page_id}' với nội dung: {comment_content}. Lỗi: {e}")

from odoo import models, fields, api
from datetime import datetime, timedelta
import base64
import logging
import requests

_logger = logging.getLogger(__name__)

class MarketingPost(models.Model):
    _name = 'marketing.post'
    _description = 'Marketing Post'

    marketing_blog_id = fields.Many2one('marketing.blog', string='Marketing Blog')
    marketing_product_id = fields.Many2one('marketing.product', string='Marketing Product', ondelete='cascade')

    account_id = fields.Many2one('manager.account', string='Account', required=True)
    page_id = fields.Many2one('facebook.page', string='Page', domain="[('account_id', '=', account_id)]")

    schedule_post = fields.Datetime(string='Đặt lịch post bài')

    comment = fields.Text(string='Comment')
    comment_suggestion_id = fields.Many2one('marketing.comment', string='Comment Suggestion')
    remind_time = fields.Selection([
        ('1', '1 minute'),
        ('2', '2 minutes'), 
        ('3', '3 minutes'),
        ('4', '4 minutes'),
        ('5', '5 minutes'),
        ('stop', 'Stop Auto Comment')
    ], string='Remind Time', default='')

    post_id = fields.Char('Post ID')
    post_url = fields.Char('Post URL')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('posted', 'Posted'),
        ('failed', 'Failed')
    ], string='Status', default='draft')
    last_auto_comment_time = fields.Datetime('Last Auto Comment Time')
    start_auto_comment = fields.Datetime(string='Start Auto Comment')
    end_auto_comment = fields.Datetime(string='End Auto Comment')

    @api.model
    def run_auto_comment_cron(self):
        _logger.info("Chạy cron job auto-comment")
        self._auto_comment()

    @api.onchange('account_id')
    def _onchange_account_id(self):
        self.page_id = False
        return {'domain': {'page_id': [('account_id', '=', self.account_id.id)]}}

    @api.onchange('comment_suggestion_id')
    def _onchange_comment_suggestion_id(self):
        if self.comment_suggestion_id:
            self.comment = self.comment_suggestion_id.name

    @api.onchange('schedule_post')
    def _onchange_schedule_post(self):
        for record in self:
            if record.schedule_post:
                record.state = 'scheduled'
                _logger.info(f"Đặt lịch post bài với ID {record.id} vào lúc {record.schedule_post}")

    def _post_scheduled_blogs(self):
        current_time = datetime.now()
        _logger.info(f"Kiểm tra các bài viết đã được lên lịch vào lúc {current_time}")
        scheduled_posts = self.search([('schedule_post', '<=', current_time), ('state', '=', 'scheduled')])
        _logger.info(f"Tìm thấy {len(scheduled_posts)} bài viết đã được lên lịch để xử lý")
        for post in scheduled_posts:
            _logger.info(f"Đang cố gắng đăng bài viết với ID {post.id}")
            post.post_blog_to_facebook()
            if post.state == 'posted':
                _logger.info(f"Đăng bài viết thành công với ID {post.id}")
            else:
                _logger.error(f"Đăng bài viết thất bại với ID {post.id}")

    def post_blog_to_facebook(self):
        for record in self:
            blog = record.marketing_blog_id.blog
            blog_title = record.marketing_blog_id.blog_title
            blog_name = blog.name
            blog_author = blog.author_id.name
            blog_image = record.marketing_blog_id.image
            blog_url = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/blog/{record.marketing_blog_id.blog.blog_id.id}/post/{record.marketing_blog_id.id}"

            post_content = (
                f"{blog_title}\n"
                f"Blog: {blog_name}\n"
                f"Tác giả: {blog_author}\n"
            )

            if record.marketing_blog_id.include_link:
                post_content += f"\nTìm hiểu thêm: {blog_url}"
                _logger.info(f"Thông tin blog URL: {blog_url}")

            _logger.info(f"Bao gồm liên kết: {record.marketing_blog_id.include_link}")
            try:
                data = {
                    'message': post_content,
                    'access_token': record.page_id.access_token,
                }
                files = {}
                if blog_image:
                    image_data = base64.b64decode(blog_image)
                    files['source'] = ('image.jpg', image_data, 'image/jpeg')

                _logger.debug(f"Đăng lên Facebook với dữ liệu: {data} và tệp: {files}")

                response = requests.post(
                    f'https://graph.facebook.com/{record.page_id.page_id}/photos',
                    data=data,
                    files=files
                )
                response.raise_for_status()
                post_data = response.json()
                record.post_id = post_data.get('id')
                record.post_url = f"https://www.facebook.com/{record.post_id.replace('_', '/posts/')}"

                comment_content = f"{blog_url}"
                comment_response = requests.post(
                    f'https://graph.facebook.com/{record.post_id}/comments',
                    data={
                        'message': comment_content,
                        'access_token': record.page_id.access_token
                    }
                )
                comment_response.raise_for_status()
                _logger.info(f"Thêm bình luận thành công với URL blog vào bài viết '{record.post_id}' trên trang '{record.page_id.page_id}'")
                record.state = 'posted'
                record.start_auto_comment = datetime.now()
                record.end_auto_comment = record.start_auto_comment + timedelta(weeks=1)

            except requests.exceptions.RequestException as e:
                record.state = 'failed'
                _logger.error(f"Đăng lên trang '{record.page_id.page_id}' hoặc thêm bình luận thất bại: {e}")
                _logger.debug(f"Nội dung phản hồi: {e.response.content if e.response else 'Không có nội dung phản hồi'}")

    def post_product_to_facebook(self):
        for record in self:
            product = record.marketing_product_id.product_id
            message = record.marketing_product_id.product_name
            product_url = record.marketing_product_id.product_url
            image = record.marketing_product_id.product_image

            post_content = message

            try:
                data = {
                    'message': post_content,
                    'access_token': record.page_id.access_token,
                }
                files = {}
                if image:
                    image_data = base64.b64decode(image)
                    files['source'] = ('image.jpg', image_data, 'image/jpeg')

                    response = requests.post(
                        f'https://graph.facebook.com/{record.page_id.page_id}/photos',
                        data=data,
                        files=files
                    )
                else:
                    response = requests.post(
                        f'https://graph.facebook.com/{record.page_id.page_id}/feed',
                        data=data
                    )
                if record.marketing_product_id.show_product_url:
                    try:
                        comment_content = f"{product_url}"
                        comment_response = requests.post(
                            f'https://graph.facebook.com/{record.post_id}/comments',
                            data={
                                'message': comment_content,
                                'access_token': record.page_id.access_token
                            }
                        )
                        comment_response.raise_for_status()
                        _logger.info(f"Thêm bình luận thành công với URL sản phẩm vào bài viết")

                    except requests.exceptions.RequestException as e:
                        _logger.error(f"Đăng lên trang thất bại: {e}")

                response.raise_for_status()
                post_data = response.json()
                record.post_id = post_data.get('id')
                record.post_url = f"https://www.facebook.com/{record.post_id.replace('_', '/posts/')}"

            except requests.exceptions.RequestException as e:
                record.state = 'failed'
                _logger.error(f"Đăng lên trang '{record.page_id.page_id}' hoặc thêm bình luận thất bại: {e}")
                _logger.debug(f"Nội dung phản hồi: {e.response.content if e.response else 'Không có nội dung phản hồi'}")

    def _post_scheduled_product(self):
        current_time = datetime.now()
        _logger.info(f"Kiểm tra các bài viết đã được lên lịch vào lúc {current_time}")
        scheduled_posts = self.search([('schedule_post', '<=', current_time), ('state', '=', 'scheduled')])
        _logger.info(f"Tìm thấy {len(scheduled_posts)} bài viết đã được lên lịch để xử lý")
        for post in scheduled_posts:
            _logger.info(f"Đang cố gắng đăng sản phẩm với ID {post.id}")
            post.post_product_to_facebook()
            if post.state == 'posted':
                _logger.info(f"Đăng sản phẩm thành công với ID {post.id}")
            else:
                _logger.error(f"Đăng sản phẩm thất bại với ID {post.id}")

    def post_comment_to_facebook(self):
        for record in self:
            comment_content = record.comment

            if not comment_content or not comment_content.strip():
                _logger.warning(f"Nội dung bình luận trống hoặc chỉ chứa khoảng trắng cho bài viết '{record.post_id}' trên trang '{record.page_id.page_id}', bỏ qua.")
                continue

            next_page = True
            page_url = f'https://graph.facebook.com/{record.post_id}/comments'

            while next_page:
                try:
                    response = requests.post(
                        page_url,
                        data={
                            'message': comment_content,
                            'access_token': record.page_id.access_token
                        }
                    )
                    response.raise_for_status()
                    _logger.info(f"Đăng bình luận thành công cho bài viết '{record.post_id}' trên trang '{record.page_id.page_id}'")

                    response_data = response.json()
                    next_page = 'paging' in response_data and 'next' in response_data['paging']
                    if next_page:
                        page_url = response_data['paging']['next']
                    else:
                        next_page = False

                except requests.exceptions.RequestException as e:
                    _logger.error(f"Đăng bình luận thất bại cho bài viết '{record.post_id}' trên trang '{record.page_id.page_id}': {e}")
                    next_page = False

    def _auto_comment(self):
        current_time = datetime.now()
        _logger.info(f"Chạy kiểm tra auto-comment lúc {current_time}")
        posts_to_comment = self.search([
            ('state', '=', 'posted'),
            ('post_id', '!=', False),
            '|', ('last_auto_comment_time', '=', False),
            ('last_auto_comment_time', '<=', current_time - timedelta(minutes=1))
        ])
        
        _logger.info(f"Tìm thấy {len(posts_to_comment)} bài viết cần comment")

        for post in posts_to_comment:
            _logger.info(f"Kiểm tra bài viết ID {post.post_id} với thời gian nhắc nhở {post.remind_time} phút")
            if post.remind_time != 'stop' and (not post.last_auto_comment_time or (current_time - post.last_auto_comment_time).total_seconds() / 60 >= int(post.remind_time)):
                if current_time >= post.end_auto_comment:
                    post.remind_time = 'stop'
                    _logger.info(f"Auto comment đã được tắt cho bài viết ID {post.post_id} vì đã đến thời gian kết thúc")
                else:
                    _logger.info(f"Đang đăng auto-comment cho bài viết ID {post.post_id}")
                    post.post_comment_to_facebook()
                    post.last_auto_comment_time = current_time
                    _logger.info(f"Thời gian auto-comment được cập nhật cho bài viết ID {post.post_id} là {post.last_auto_comment_time}")
            elif post.remind_time == 'stop':
                _logger.info(f"Auto comment đã được tắt cho bài viết ID {post.post_id}")
    def post_random_comment_to_facebook(self):
        self.ensure_one()
        comment_content = self.comment

        if not comment_content or not comment_content.strip():
            _logger.warning(f"Nội dung bình luận trống hoặc chỉ chứa khoảng trắng cho bài viết '{self.post_id}', bỏ qua.")
            return

        try:
            response = requests.post(
                f'https://graph.facebook.com/{self.post_id}/comments',
                data={
                    'message': comment_content,
                    'access_token': self.page_id.access_token
                }
            )
            response.raise_for_status()
            _logger.info(f"Đăng bình luận tự động thành công cho bài viết '{self.post_id}' trên trang '{self.page_id.page_id}' với nội dung: {comment_content}")
        except requests.exceptions.RequestException as e:
            _logger.error(f"Đăng bình luận tự động thất bại cho bài viết '{self.post_id}' trên trang '{self.page_id.page_id}' với nội dung: {comment_content}. Lỗi: {e}")
