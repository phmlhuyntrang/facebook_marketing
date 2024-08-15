from odoo import models, fields, api
from odoo.addons.http_routing.models.ir_http import slug

class BlogMarketingContent(models.Model):
    _name = 'marketing.blog'
    _description = 'Blog Marketing Content'
    _inherits = {'marketing.content': 'content_id'}

    content_id = fields.Many2one('marketing.content', string='Marketing Content', required=True, ondelete='cascade', auto_join=True)
    blog_id = fields.Many2one('blog.post', string='Blog')
    temp_image = fields.Binary(string='Temporary Image', attachment=False)
    
    @api.model
    def create(self, vals):
        # Tạo bản ghi marketing.content 
        content_vals = {
            'content': vals.get('content', ''),
            'url': vals.get('url', ''),
            'include_link': vals.get('include_link', False)
        }
        content = self.env['marketing.content'].create(content_vals)
        vals['content_id'] = content.id

        res = super(BlogMarketingContent, self).create(vals)
        
        if res.temp_image:
            image = self.env['marketing.content.image'].create({
                'content_id': res.content_id.id,
                'image': res.temp_image,
                'datas': res.temp_image,
            })
            res.content_id.write({'image_ids': [(4, image.id)]})
            res.temp_image = False
        
        return res

    def write(self, vals):
        # Cập nhật bản ghi marketing.content
        content_vals = {}
        if 'content' in vals:
            content_vals['content'] = vals['content']
        if 'url' in vals:
            content_vals['url'] = vals['url']
        if 'include_link' in vals:
            content_vals['include_link'] = vals['include_link']
        
        if content_vals:
            self.content_id.write(content_vals)

        res = super(BlogMarketingContent, self).write(vals)
        
        if vals.get('temp_image'):
            image = self.env['marketing.content.image'].create({
                'content_id': self.content_id.id,
                'image': self.temp_image,
                'datas': self.temp_image,
            })
            self.content_id.write({'image_ids': [(4, image.id)]})
            self.temp_image = False
        
        return res

    @api.onchange('blog_id')
    def _onchange_blog_post(self):
        if self.blog_id:
            self.content = self.blog_id.name
            self.url = '/blog/%s/post/%s' % (slug(self.blog_id.blog_id), slug(self.blog_id))
