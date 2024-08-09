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
    product_image = fields.Binary(string='Image')
    # product_url = fields.Char(string='Link', compute='_compute_product_url', store=True)
    product_name = fields.Char( string='Content')
    show_product_url = fields.Boolean(string="Include Link in Post", default=True)

    post_ids = fields.One2many('marketing.post', 'marketing_product_id', string='Posts')
    
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
                
    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            self.product_name = self.product_id.name
            self.product_image = self.product_id.image_1920