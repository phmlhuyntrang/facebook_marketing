from odoo import models, fields


class MarketingPost(models.Model):
    _name = 'marketing.post'
    _description = 'Marketing Post'

    marketing_product_id = fields.Many2one('marketing.product', string='Marketing Product')
    marketing_blog_id = fields.Many2one('marketing.blog', string='Marketing Blog')

    page_id = fields.Many2one('facebook.page', string='Facebook Page')
    post_id = fields.Char('Post ID')
    post_url = fields.Char('Post URL')
    state = fields.Selection([
        ('posted', 'Posted'),
        ('failed', 'Failed')
    ], string='Status', default='posted')
