import requests
import json
from odoo import models, fields, api
from datetime import datetime, timedelta
import base64
import logging
import random
from odoo.addons.http_routing.models.ir_http import slug
from odoo.http import request

_logger = logging.getLogger(__name__)

class MarketingPost(models.Model):
    _name = 'marketing.post'
    _description = 'Marketing Post'

    content_id = fields.Many2one('marketing.content', string='Content', default=lambda self: self._get_latest_content())
    
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
    last_auto_comment_time = fields.Datetime('Last Auto Comment Time')
    start_auto_comment = fields.Datetime(string='Start Auto Comment')
    end_auto_comment = fields.Datetime(string='End Auto Comment')

    post_id = fields.Char('Post ID')
    post_url = fields.Char('Post URL')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('posted', 'Posted'),
        ('failed', 'Failed')
    ], string='Status', default='draft')
    # Chọn content mới nhất được lưu
    @api.model
    def _get_latest_content(self):
        return self.env['marketing.content'].search([], order='create_date desc', limit=1).id

    @api.model
    def create(self, vals):
        if 'content_id' not in vals:
            vals['content_id'] = self._get_latest_content()
        return super(MarketingPost, self).create(vals)

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
                record.start_auto_comment = record.schedule_post
                record.end_auto_comment = record.start_auto_comment + timedelta(weeks=1)
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

    def post_to_facebook(self):
        content = self.content_id.content or "Không lấy được content"
        logging.info("-----------------------------------------------------------------")
        logging.info("%s \n\n\n\n", self.content_id)
        
        images = self.content_id.image_ids
        
        try:
            access_token = self.page_id.access_token
            page_id = self.page_id.page_id

            # Tải lên từng ảnh riêng lẻ
            media_ids = []
            for idx, attachment in enumerate(images):
                _logger.info(f"Available fields for attachment: {attachment._fields.keys()}")
                _logger.info(f"Attachment data: {attachment.read()}")
                
                image_data = attachment.image or attachment.datas
                if not image_data:
                    _logger.warning(f"Ảnh {idx} không có dữ liệu, bỏ qua.")
                    continue
                
                image_data = base64.b64decode(image_data)
                files = {f'file{idx}': (f'image{idx}.jpg', image_data, 'image/jpeg')}
                photo_data = {
                    'access_token': access_token,
                    'published': False  # Không đăng ảnh ngay lập tức
                }
                photo_response = requests.post(
                    f'https://graph.facebook.com/{page_id}/photos',
                    data=photo_data,
                    files=files
                )
                photo_response.raise_for_status()
                media_ids.append({'media_fbid': photo_response.json()['id']})

            # Tạo bài đăng với tất cả ảnh đã tải lên
            data = {
                'message': content,
                'access_token': access_token,
                'attached_media': json.dumps(media_ids)
            }

            _logger.info(f"Attempting to post to page {page_id}")
            _logger.info(f"Data being sent: {data}")
            _logger.info(f"Number of images being sent: {len(media_ids)}")

            response = requests.post(
                f'https://graph.facebook.com/{page_id}/feed',
                data=data
            )

            _logger.info(f"Response status code: {response.status_code}")
            _logger.info(f"Response content: {response.content}")

            response.raise_for_status()
            post_data = response.json()
            self.post_id = post_data.get('id')
            self.post_url = f"https://www.facebook.com/{self.post_id.replace('_', '/posts/')}"

            if self.content_id.include_link and self.content_id.link:
                try:
                    comment_response = requests.post(
                        f'https://graph.facebook.com/{self.post_id}/comments',
                        data={
                            'message': self.content_id.link,
                            'access_token': access_token
                        }
                    )
                    comment_response.raise_for_status()
                    _logger.info(f"Thêm bình luận thành công với URL sản phẩm vào bài viết")
                except requests.exceptions.RequestException as e:
                    _logger.error(f"Thêm bình luận URL thất bại : {e}")
                    _logger.error(f"Comment response content: {e.response.content if e.response else 'No response content'}")

            self.state = 'posted'
            self.start_auto_comment = datetime.now()
            self.end_auto_comment = self.start_auto_comment + timedelta(weeks=1)
        
        except requests.exceptions.RequestException as e:
            self.state = 'failed'
            _logger.error(f"Đăng lên trang '{page_id}' thất bại: {e}")
            _logger.error(f"Response content: {e.response.content if e.response else 'No response content'}")
            _logger.debug(f"Nội dung phản hồi: {e.response.content if e.response else 'Không có nội dung phản hồi'}")
        
    def post_comment_to_facebook(self, comment_content):
        page_url = f'https://graph.facebook.com/{self.post_id}/comments'
        try:
            response = requests.post(
                page_url,
                data={
                    'message': comment_content,
                    'access_token': self.page_id.access_token
                }
            )
            response.raise_for_status()
            _logger.info(f"Đăng bình luận thành công cho bài viết '{self.post_id}' trên trang '{self.page_id.page_id}'")

        except requests.exceptions.RequestException as e:
            _logger.error(f"Đăng bình luận thất bại cho bài viết '{self.post_id}' trên trang '{record.page_id.page_id}': {e}")

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
                    post.post_random_comment_to_facebook()
                    post.last_auto_comment_time = current_time
                    _logger.info(f"Thời gian auto-comment được cập nhật cho bài viết ID {post.post_id} là {post.last_auto_comment_time}")
            elif post.remind_time == 'stop':
                _logger.info(f"Auto comment đã được tắt cho bài viết ID {post.post_id}")
                
    def post_random_comment_to_facebook(self):
        self.ensure_one()
        comment_suggestions = self.env['marketing.comment'].search([])
        if not comment_suggestions:
            _logger.warning(f"Không tìm thấy comment suggestion nào để đăng cho bài viết '{self.post_id}' trên trang '{self.page_id.page_id}', bỏ qua.")
            return

        random_comment = random.choice(comment_suggestions).name
        self.post_comment_to_facebook(random_comment)