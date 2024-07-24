
import logging
from odoo import models, fields, api
import requests
import base64
import io

class Facebookvalueing(models.Model):
    _name = 'manager.account'
    _description = 'Load account facebook information'

    account_id = fields.Char(string='Account ID', required=True)
    access_token = fields.Text('Access Token', required=True)
    account_name = fields.Char('User Name')
    account_avatar = fields.Binary('Avatar')
    page_name = fields.Char('Page')
    page_id = fields.Char('Page ID')
    category_id = fields.Char('Page Category')
    category_name = fields.Char('Category ID')
    
    def load_data(self):
        flag = False
        response = None
        id = self.env.context.get("id")
        for value in self:
            if value.id == id:
                url_info_request = f'https://graph.facebook.com/v20.0/{value.account_id}?access_token={value.access_token}'  
                url_avatar_request = f'https://graph.facebook.com/v20.0/{value.account_id}/picture?access_token={value.access_token}'  

                try:
                    info_response = requests.get(url_info_request)
                    avatar_response = requests.get(url_avatar_request)
                    info_response.raise_for_status()
                    avatar_response.raise_for_status()
                    info_data = info_response.json()
                    # avatar_data = avatar_response.json()
                    flag = True
                    # logging.info(avatar_data)
                    if flag == True:
                        self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                            'title': 'Thành công',
                            'message': 'Thành công!',
                            'type': 'success',
                        })
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
    
#     ///
# import requests

# def get_facebook_account_info(user_id, access_token):
#     base_url = "https://graph.facebook.com/v18.0/"
#     fields = "id,name,email,gender,birthday,link"
    
#     url = f"{base_url}{user_id}?fields={fields}&access_token={access_token}"
    
#     try:
#         response = requests.get(url)
#         response.raise_for_status()
#         data = response.json()
#         return data
#     except requests.exceptions.RequestException as e:
#         print(f"Đã xảy ra lỗi khi gọi API: {e}")
#         return None

# # Sử dụng hàm
# user_id = input("Nhập Facebook ID: ")
# access_token = input("Nhập Access Token: ")

# account_info = get_facebook_account_info(user_id, access_token)

# if account_info:
#     print("Thông tin tài khoản Facebook:")
#     for key, value in account_info.items():
#         print(f"{key}: {value}")
# else:
#     print("Không thể lấy thông tin tài khoản.")