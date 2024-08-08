import logging
from venv import logger
import requests
from odoo import models, fields, api # type: ignore
from odoo.addons.http_routing.models.ir_http import slug
from odoo.http import request
from datetime import datetime

class MarketingProduct(models.Model):
    _name = 'marketing.product'
    _description = 'Integrate Facebook to marketing product'

    product_id = fields.Many2one('product.template', string='Product', required=True)
    product_image = fields.Image(related='product_id.image_1920', string='Product Image')
    product_name = fields.Char(related='product_id.name', string='Product Name')
    product_url = fields.Char(string='Link', compute='_compute_product_url', store=True)
    show_product_url = fields.Boolean(string="Include Link in Post", default=True)

    post_ids = fields.One2many('marketing.post', 'marketing_product_id', string='Posts')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('failed', 'Failed')
    ], string='Status', default='draft', compute='_compute_state', store=True)
    
    @api.depends('product_id', 'show_product_url')
    def _compute_product_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.product_id and record.show_product_url:
                record.product_url = f"{base_url}/shop/product/{slug(record.product_id)}"
            else:
                record.product_url = False

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
