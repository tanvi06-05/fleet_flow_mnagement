from odoo import api, fields, models, _


class FleetFlowMaintenance(models.Model):
    _name = 'fleet.flow.maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'FleetFlow Maintenance'
    _order = 'date desc, id desc'

    vehicle_id = fields.Many2one(
        'fleet.flow.vehicle',
        string='Vehicle',
        required=True,
        tracking=True,
    )
    service_type = fields.Selection(
        selection=[
            ('preventive', 'Preventive'),
            ('reactive', 'Reactive'),
        ],
        string='Service Type',
        required=True,
        default='preventive',
        tracking=True,
    )
    description = fields.Text(
        string='Description',
        required=True,
    )
    cost = fields.Float(string='Cost', tracking=True)
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('planned', 'Planned'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
        ],
        string='Status',
        default='planned',
        required=True,
        tracking=True,
    )
    mechanic = fields.Char(string='Mechanic / Vendor')
    notes = fields.Html(string='Notes')

    vehicle_name = fields.Char(
        related='vehicle_id.name',
        string='Vehicle Name',
        store=True,
    )

    def action_start(self):
        for rec in self:
            rec.state = 'in_progress'
            rec.vehicle_id.status = 'in_shop'

    def action_complete(self):
        for rec in self:
            rec.state = 'completed'
            open_maintenance = self.search([
                ('vehicle_id', '=', rec.vehicle_id.id),
                ('state', 'in', ['planned', 'in_progress']),
                ('id', '!=', rec.id),
            ])
            if not open_maintenance:
                rec.vehicle_id.status = 'available'
