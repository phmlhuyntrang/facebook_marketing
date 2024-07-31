import json
import logging
from odoo import models, fields, api
import requests
import base64
import io

class ManagerAccount(models.Model):
    _name = 'manager.account'
    _description = 'Load account facebook information'
    
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    # Thêm trường này
    is_favorite = fields.Boolean(string="Favorite", default=False, tracking=True)
    
    account_id = fields.Char(string='Account ID', required=True)
    access_token = fields.Text('Access Token', required=True)
    account_name = fields.Char('User Name')
    account_avatar = fields.Binary('Avatar')

    page_ids = fields.One2many('facebook.page', 'account_id', string="Pages")

    def load_data(self):
        for record in self:
            record.load_account_info()
            record.load_account_ava()
            record.load_pages()
        return True
       
    def load_account_info(self):
        url_info_request = f'https://graph.facebook.com/v20.0/{self.account_id}?access_token={self.access_token}'  
        try:
            info_response = requests.get(url_info_request)
            info_data = info_response.json()

            # logging.info(info_data)

            #set fields
            self.account_name = info_data['name']

        except requests.exceptions.RequestException as e:
            print(f"Đã xảy ra lỗi khi gọi API Get account info: {e}")
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': 'Lỗi',
                'message': f"Đã xảy ra lỗi khi gọi API: {e}",
                'type': 'danger',
            })
        return None

    
    def load_account_ava(self):
        url_avatar_request = f'https://graph.facebook.com/v20.0/{self.account_id}/picture?type=large&access_token={self.access_token}'
        try:
            avatar_response = requests.get(url_avatar_request)

            #set fields
            self.account_avatar = base64.b64encode(avatar_response.content).decode('utf-8')

        except requests.exceptions.RequestException as e:
            print(f"Đã xảy ra lỗi khi gọi API Get Avatar: {e}")
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': 'Lỗi',
                'message': f"Đã xảy ra lỗi khi gọi API: {e}",
                'type': 'danger',
            })
        return None
    

    def load_pages(self):
        url_pages_request = f'https://graph.facebook.com/v20.0/{self.account_id}/accounts?access_token={self.access_token}'
        try:
            pages_response = requests.get(url_pages_request)
            page_data = pages_response.json()

            if page_data and 'data' in page_data:
                for page in page_data['data']:
                    # Tạo hoặc cập nhật Facebook Page
                    facebook_page = self.env['facebook.page'].search([('page_id', '=', page['id'])], limit=1)
                    if not facebook_page:
                        facebook_page = self.env['facebook.page'].create({
                            'account_id': self.id,
                            'page_name': page['name'],
                            'page_id': page['id'],
                            'page_avatar': self.get_pages_ava(page['id']),
                            'access_token': page['access_token'],
                            'category': page['category']
                        })
                    else:
                        facebook_page.write({
                            'page_name': page['name'],
                            'page_avatar': self.get_pages_ava(page['id']),
                            'access_token': page['access_token'],
                            'category': page['category']
                        })

                    # Xử lý các category
                    category_ids = []
                    if 'category_list' in page:
                        for category in page['category_list']:
                            fb_category = self.env['facebook.category'].search([('fb_category_id', '=', category['id'])], limit=1)
                            if fb_category:
                                category_ids.append(fb_category.id)
                            else:
                                # Nếu category không tồn tại, bạn có thể quyết định tạo mới hoặc bỏ qua
                                new_category = self.env['facebook.category'].create({
                                    'fb_category_name': category['name'],
                                    'fb_category_id': category['id'],
                                })
                                category_ids.append(new_category.id)
                        
                    # Cập nhật các category cho Facebook Page
                    facebook_page.write({
                        'category_ids': [(6, 0, category_ids)]
                    })

        except requests.exceptions.RequestException as e:
            print(f"Đã xảy ra lỗi khi gọi API Get Page: {e}")
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': 'Lỗi',
                'message': f"Đã xảy ra lỗi khi gọi API: {e}",
                'type': 'danger',
            })
        return None
    
    def get_pages_ava(self, page_id):
        url_page_ava_request = f'https://graph.facebook.com/v20.0/{page_id}/picture?type=large&access_token={self.access_token}'
        try:
            avatar_page_response = requests.get(url_page_ava_request)
            return base64.b64encode(avatar_page_response.content)
            # logging.info(base64.b64encode(avatar_page_response.content))
            # return base64.b64encode(avatar_page_response.content)

        except requests.exceptions.RequestException as e:
            print(f"Đã xảy ra lỗi khi gọi API Get Avatar Page: {e}")
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': 'Lỗi',
                'message': f"Đã xảy ra lỗi khi gọi API: {e}",
                'type': 'danger',
            })
            return None   
        
    def toggle_favorite(self):
        for record in self:
            record.is_favorite = not record.is_favorite