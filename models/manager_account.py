import json
import logging
from odoo import models, fields, api
import requests
import base64
import io

class ManagerAccount(models.Model):
    _name = 'manager.account'
    _description = 'Load account facebook information'

    account_id = fields.Char(string='Account ID', required=True)
    access_token = fields.Text('Access Token', required=True)
    account_name = fields.Char('User Name')
    account_avatar = fields.Binary('Avatar')

    page_name = fields.Char(string="Name")
    page_id = fields.Char(string="Page ID")
    category = fields.Char(string="Category")
    category_list = fields.Text(string="Category List")

    @api.model
    def load_data(self):
        flag = False
        response = None
        id = self.env.context.get("id")
        for value in self:
            if value.id == id:
                url_info_request = f'https://graph.facebook.com/v20.0/{value.account_id}?access_token={value.access_token}'  
                url_avatar_request = f'https://graph.facebook.com/v20.0/{value.account_id}/picture?type=large&access_token={value.access_token}'  
                url_pages_request = f'https://graph.facebook.com/v20.0/{value.account_id}/accounts?access_token={value.access_token}'

                try:
                    info_response = requests.get(url_info_request)
                    avatar_response = requests.get(url_avatar_request)
                    pages_response = requests.get(url_pages_request)

                    info_response.raise_for_status()
                    avatar_response.raise_for_status()
                    # pages_response.raise_for_status()

                    info_data = info_response.json()
                    page_data = pages_response.json()
                    # avatar_data = avatar_response.json()

                    pages = []
                    if pages_response.status_code == 200:
                        pages = pages_response.json().get('data', [])
                        # Save or Update Pages in Odoo
                        for page in pages:
                            # Check if page already exists
                            existing_page = self.search([('page_id', '=', page.get('id'))], limit=1)
                            category_names = [category['name'] for category in page.get('category_list', [])]
                            # Chuyển danh sách tên thành chuỗi JSON
                            category_names_json = json.dumps(category_names, ensure_ascii=False)
                            # Mã hóa chuỗi JSON để lưu vào trường category_list
                            category_names_decoded = json.loads(category_names_json)
                            category_names_str = ', '.join(category_names_decoded)
                            if existing_page:
                                # Update existing page
                                existing_page.write({
                                    'page_name': page.get('name'),   
                                    'category': page.get('category'),
                                    'access_token': page.get('access_token'),
                                    'category_list':  category_names_str
                                })
                            else:
                                # Create new page
                                self.create({
                                    'page_name': page.get('name'),
                                    'page_id': page.get('id'),
                                    'category': page.get('category'),
                                    'access_token': page.get('access_token'),
                                    'category_list':  category_names_str
                                })
                    else:
                        {
                        _logger.error("Không thể kết nối với Facebook API. Mã lỗi: %s", response.status_code,response.text)
                        }
                    
                    # //notification
                    flag = True
                    logging.info(page_data)
                    if flag == True:
                        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                            'title': 'Thành công',
                            'message': 'Thành công!',
                            'type': 'success',
                        })

                    #set fields
                    value.account_name = info_data['name']
                    value.account_avatar = base64.b64encode(avatar_response.content).decode('utf-8')

                except requests.exceptions.RequestException as e:
                    print(f"Đã xảy ra lỗi khi gọi API: {e}")
                    self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                        'title': 'Lỗi',
                        'message': f"Đã xảy ra lỗi khi gọi API: {e}",
                        'type': 'danger',
                    })
        
                    return None
    # @api.model
    # def load_data(self, account_id=None):
    #     if not account_id:
    #         return False

    #     account = self.search([('id', '=', account_id)], limit=1)
    #     if not account:
    #         return False

    #     url_info_request = f'https://graph.facebook.com/v20.0/{account.account_id}?access_token={account.access_token}'  
    #     url_avatar_request = f'https://graph.facebook.com/v20.0/{account.account_id}/picture?type=large&access_token={account.access_token}'  
    #     url_pages_request = f'https://graph.facebook.com/v20.0/{account.account_id}/accounts?access_token={account.access_token}'

    #     try:
    #         info_response = requests.get(url_info_request)
    #         avatar_response = requests.get(url_avatar_request)
    #         pages_response = requests.get(url_pages_request)

    #         info_response.raise_for_status()
    #         avatar_response.raise_for_status()

    #         info_data = info_response.json()
    #         page_data = pages_response.json()

    #         if pages_response.status_code == 200:
    #             pages = pages_response.json().get('data', [])
    #             for page in pages:
    #                 existing_page = self.env['manager.account'].search([('page_id', '=', page.get('id'))], limit=1)
    #                 category_names = [category['name'] for category in page.get('category_list', [])]
    #                 category_names_str = ', '.join(category_names)
                    
    #                 page_values = {
    #                     'page_name': page.get('name'),
    #                     'category': page.get('category'),
    #                     'access_token': page.get('access_token'),
    #                     'category_list': category_names_str
    #                 }
                    
    #                 if existing_page:
    #                     existing_page.write(page_values)
    #                 else:
    #                     page_values['page_id'] = page.get('id')
    #                     self.env['manager.account'].create(page_values)

    #         account.write({
    #             'account_name': info_data['name'],
    #             'account_avatar': base64.b64encode(avatar_response.content).decode('utf-8')
    #         })

    #         self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
    #             'title': 'Thành công',
    #             'message': 'Thành công!',
    #             'type': 'success',
    #         })

    #         return True

    #     except requests.exceptions.RequestException as e:
    #         _logger.error(f"Đã xảy ra lỗi khi gọi API: {e}")
    #         self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
    #             'title': 'Lỗi',
    #             'message': f"Đã xảy ra lỗi khi gọi API: {e}",
    #             'type': 'danger',
    #         })
    #         return False