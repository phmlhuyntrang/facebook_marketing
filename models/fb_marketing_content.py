from odoo import models, fields, api
from odoo.addons.http_routing.models.ir_http import slug

class MarketingContent(models.Model):
    _name = 'marketing.content'
    _description = 'Marketing Content'

    blog = fields.Many2one('blog.post', string='Blog', required=False)
    product = fields.Many2one('product.template', string='Product', required=False)
    product_image = fields.Image(related='product.image_1920', string='Product Image')

    post = fields.One2many('marketing.post', 'content_id', string='Posts')

    image = fields.Binary(string='Image')
    content = fields.Text(string='Content')
    link = fields.Char(string='Link')
    include_link = fields.Boolean(string='Include Link in Post', default=True)
    author = fields.Char(string='Author')

    type = fields.Selection([
        ('blog', 'Blog'),
        ('product', 'Product')
    ], string='Type')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('failed', 'Failed')
    ], string='Status', default='draft', compute='_compute_state', store=True)
    
    @api.depends('post.state')
    def _compute_state(self):
        for record in self:
            post_states = set(record.post.mapped('state'))
            if not post_states:
                record.state = 'draft'
            elif post_states == {'posted'}:
                record.state = 'posted'
            elif 'failed' in post_states:
                record.state = 'failed'
            else:
                record.state = 'draft'

    @api.onchange('product', 'blog')
    def _onchange_product_or_blog(self):
        if self.product:
            self.type = 'product'
            self.content = self.product.name
            self.image = self.product_image
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            self.link =  f"{base_url}/shop/product/{slug(self.product)}"
        elif self.blog:
            self.type = 'blog'
            self.content = self.blog.name
            self.link = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/blog/{self.blog.blog_id.id}/post/{self.blog.id}"
            self.author = self.blog.author_id.name
        # Tự động lưu sau khi cập nhật dữ liệu
    #     self.auto_save()

    # def auto_save(self):
    #     # Kiểm tra xem bản ghi đã tồn tại chưa
    #     if not self.id:
    #         # Nếu chưa tồn tại, tạo mới
    #         self.create({
    #             'blog': self.blog.id if self.blog else False,
    #             'product': self.product.id if self.product else False,
    #             'image': self.image,
    #             'content': self.content,
    #             'link': self.link,
    #             'include_link': self.include_link,
    #         })
    #     else:
    #         # Nếu đã tồn tại, cập nhật
    #         self.write({
    #             'blog': self.blog.id if self.blog else False,
    #             'product': self.product.id if self.product else False,
    #             'image': self.image,
    #             'content': self.content,
    #             'link': self.link,
    #             'include_link': self.include_link,
    #         })