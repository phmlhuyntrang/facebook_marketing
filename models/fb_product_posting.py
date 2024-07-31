from odoo import _, fields, models # type: ignore
from odoo.addons.http_routing.models.ir_http import slug # type: ignore
from odoo.http import request # type: ignore

class ProductPosting(models.Model):
    _inherit = "product.template"

    website_preview_url = fields.Html("Preview", sanitize = False, compute = 'preview_set_up') # Iframe for preview product
    mobile_view = fields.Boolean("Mobile", default=False) # Change to mobile view radio
    show_preview = fields.Boolean("Show Preview", default=False) # Show product preview in product template check-box

    # Toggle publish in product template page
    def toggle_publish(self):
        for record in self:
            record.website_published = not record.website_published
        return True

    # Reload UI
    def refesh_iframe(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    # Change UI to mobile
    def change_view_mode(self):
        id = self.env.context.get("id")
        for product in self:
            if(product.id == id):
                product.mobile_view = not product.mobile_view

    # Khởi tạo iframe hiển thị preview
    def preview_set_up(self):
        for product in self:
            url = f"{request.httprequest.host_url}shop/{slug(product)}" # -> https://localhost:3069/shop/abc-1 
            if(product.mobile_view == True):
                product.website_preview_url = f'<div class="smartphone_view"><iframe src="{url}" class="shadow" id="preview_iframe"><p>Your browser does not support iframes.</p></iframe></div>'
            else:
                product.website_preview_url = f'<div class="pc_view"><iframe src="{url}" class="shadow" id="preview_iframe" height="24rem"><p>Your browser does not support iframes.</p></iframe><div class="pc_view_power"></div></div>'