import requests
from odoo import models, fields, api
from datetime import datetime, timedelta
import base64
import logging
from odoo.addons.http_routing.models.ir_http import slug # type: ignore
from odoo.http import request # type: ignore

_logger = logging.getLogger(__name__)

class MarketingPost(models.Model):
    _name = 'marketing.post'
    _description = 'Marketing Post'

    # marketing_blog_id = fields.Many2one('marketing.blog', string='Marketing Blog')
    # marketing_product_id = fields.Many2one('marketing.product', string='Marketing Product', ondelete='cascade')

    content_id = fields.Many2one('marketing.content', string='Content')

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

    def _post_scheduled(self):
        current_time = datetime.now()
        _logger.info(f"Kiểm tra các bài viết đã được lên lịch vào lúc {current_time}")
        scheduled_posts = self.search([('schedule_post', '<=', current_time), ('state', '=', 'scheduled')])
        _logger.info(f"Tìm thấy {len(scheduled_posts)} bài viết đã được lên lịch để xử lý")
        for post in scheduled_posts:
            _logger.info(f"Đang cố gắng đăng bài viết với ID {post.id}")
            post.post_to_facebook()
            if post.state == 'posted':
                _logger.info(f"Đăng bài viết thành công với ID {post.id}")
            else:
                _logger.error(f"Đăng bài viết thất bại với ID {post.id}")

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

    def post_to_facebook(self):
        for record in self:
            # lấy dữ liệu
            # if not record.content_id:
            #     _logger.error(f"\n\n\n\nKhông tìm thấy content_id cho bài đăng với ID {record.content_id.id}")
            #     record.state = 'failed'
                
            content = record.content_id.content or "Không lấy được content"
            logging.info("-----------------------------------------------------------------")
            logging.info("%s \n\n\n\n",record.content_id)
                
            image = record.content_id.image
            content_url = record.content_id.link

            # kiểm tra nếu đang chọn blog thì lấy thêm thông tin tác giả
            # if record.marketing_blog_id:
            #     blog_name = record.marketing_blog_id.blog.name
            #     blog_author = record.marketing_blog_id.blog.author_id.name
            #     content += (
            #         f"\n"
            #         f"Blog: {blog_name}\n"
            #         f"Tác giả: {blog_author}\n"
            #     )

            try:
                data = {
                    'message': content,
                    'access_token': record.page_id.access_token,
                }
                # Kiểm tra đăng có/không hình ảnh
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
                                
                response.raise_for_status()
                post_data = response.json()
                record.post_id = post_data.get('id')
                record.post_url = f"https://www.facebook.com/{record.post_id.replace('_', '/posts/')}"
                
                # Thêm comment chứa URL của product
                if record.content_id.include_link and content_url:
                    try:
                        comment_response = requests.post(
                            f'https://graph.facebook.com/{record.post_id}/comments',
                            data={
                                'message': content_url,
                                'access_token': record.page_id.access_token
                            }
                        )
                        comment_response.raise_for_status()
                        _logger.info(f"Thêm bình luận thành công với URL sản phẩm vào bài viết")

                    except requests.exceptions.RequestException as e:
                        logging.error(f"Thêm bình luận URL thất bại : {e}")
          
                record.state = 'posted'
                record.start_auto_comment = datetime.now()
                record.end_auto_comment = record.start_auto_comment + timedelta(weeks=1)

            except requests.exceptions.RequestException as e:
                record.state = 'failed'
                _logger.error(f"Đăng lên trang '{record.page_id.page_id}' thất bại: {e}")
                _logger.debug(f"Nội dung phản hồi: {e.response.content if e.response else 'Không có nội dung phản hồi'}")