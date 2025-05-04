from odoo import models, fields, api

class SimpleTodoModel(models.Model):
    _name = 'simple_todo.model'
    _description = 'Simple Todo Model'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
