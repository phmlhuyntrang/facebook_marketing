from odoo import models, fields

class FacebookPostLine(models.Model):
    _name = 'facebook.post.line'
    _description = 'Facebook Post Line'

    marketing_post_id = fields.Many2one('marketing.post', string='Marketing Post', required=True, ondelete='cascade')
    # page_id = fields.Many2one('facebook.page', string='Page', readonly=True)  # Change to Many2one to reference the correct model
    post_id = fields.Char(string='Facebook Post ID', readonly=True)
    post_url = fields.Char(string='Facebook Post URL', readonly=True)