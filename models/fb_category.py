from odoo import models, fields, api # type: ignore
import logging
import json
import requests

_logger = logging.getLogger(__name__)

class FacebookCategory(models.Model):
    _name = 'facebook.category'
    _description = 'Facebook Categories List'

    # Các trường dữ liệu của model
    fb_category_name = fields.Char(string='Category Name')
    fb_category_id = fields.Char(string='Category ID')
    parent_category = fields.Many2one('facebook.category', string='Parent Category', index=True, ondelete='set null')
    # parent_category_name = fields.Char(string='Parent Category Name', related='parent_category.fb_category_name', store=True)
    parent_category_path = fields.Char(string='Parent Path')
    blog_category = fields.Many2many('blog.tag.category', string='Blog Categories')
    product_category = fields.Many2many('product.public.category', string='Product Categories')
    def _format_category_name(self, category):
        # Giả sử phương thức này định dạng tên danh mục theo một cách nào đó
        return category.get('name', '').strip().title()

    def _create_or_update_category(self,categories,parent_category_id, parent_category_path):
        for category in categories:
            # Tạo hoặc cập nhật danh mục và các danh mục con
            fb_category_name = category.get('name')
            fb_category_id = category.get('id')
            path = parent_category_path + '/' + fb_category_name
            
            category_record = self.create({
                'fb_category_name': fb_category_name,
                'fb_category_id': fb_category_id,
                'parent_category': parent_category_id,
                # 'parent_category_name': parent_category_name,
                'parent_category_path': path, 
            })

            subcategories = category.get('fb_page_categories', [])
            if subcategories:
                self._create_or_update_category(subcategories, category_record.id, category_record.parent_category_path)

    @api.model
    def fetch_facebook_categories(self):
        access_token = self.env['ir.config_parameter'].sudo().get_param('facebook.api_token')
        
        url = f"https://graph.facebook.com/v20.0/fb_page_categories?access_token={access_token}"
        response = requests.get(url)
        
        if response.status_code == 200:
            categories = response.json().get('data', [])
            _logger.info("Kết nối thành công với Facebook API để lấy danh sách category.")
            
            parent_category = self.create({
                'fb_category_name': None,
                'fb_category_id': None,
                'parent_category': None,
                'parent_category_path': None,
            })
            parent_category_path = ''
            self._create_or_update_category(categories, parent_category.id, parent_category_path)

        else:
            _logger.error("Không thể kết nối với Facebook API để lấy category facebook. Mã lỗi: %s, Phản hồi: %s", response.status_code, response.text)


