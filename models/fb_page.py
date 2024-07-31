from odoo import models, fields, api


class FacebookPage(models.Model):
    _name = 'facebook.page'
    _description = 'Facebook Page'

    # _inherit = ['mail.thread', 'mail.activity.mixin']

    account_id = fields.Many2one('manager.account', string='Account')
    page_avatar = fields.Binary('Avatar')
    page_name = fields.Char(string="Name")
    page_id = fields.Char(string="Page ID")
    access_token = fields.Char(string="Access Token")
    category = fields.Char(string="Main Category")
    category_ids = fields.Many2many('facebook.category', string='Categories', 
                                    relation='facebook_page_category_rel',
                                    column1='page_id', column2='category_id')
    
   
    is_favorite = fields.Boolean(string="Favorite", default=False, tracking=True)

   
    def toggle_favorite(self):
        for record in self:
            record.is_favorite = not record.is_favorite