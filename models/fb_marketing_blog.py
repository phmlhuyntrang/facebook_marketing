
import logging
import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class MarketingBlog(models.Model):
    _name = 'marketing.blog'
    _description = 'Marketing Blog'

    blog = fields.Many2one('blog.post', string='Blog', required=True)
    blog_title = fields.Text(string='Blog content')
    account_ids = fields.Many2many('manager.account', string='Account', required=True)
    page_ids = fields.Many2many('facebook.page', string='Page')
    post_ids = fields.One2many('marketing.post', 'marketing_blog_id', string='Posts')
    comment = fields.Text(string='Comment')
    image = fields.Binary(string='Image')
    link = fields.Char(string='Link')
    include_link = fields.Boolean(string='Include Link in Post', default=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('failed', 'Failed')
    ], string='Status', default='draft', compute='_compute_state', store=True)
    
    @api.depends('post_ids.state')
    def _compute_state(self):
        for record in self:
            post_states = set(record.post_ids.mapped('state'))
            if not post_states:
                record.state = 'draft'
            elif post_states == {'posted'}:
                record.state = 'posted'
            elif 'failed' in post_states:
                record.state = 'failed'
            else:
                record.state = 'draft'

    @api.onchange('blog')
    def _onchange_blog(self):
        if self.blog:
            self.blog_title = self.blog.name
            self.link = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/blog/{self.blog.blog_id.id}/post/{self.blog.id}"