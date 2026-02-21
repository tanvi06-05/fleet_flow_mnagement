from odoo import api, fields, models


class FleetFlowFuelExpense(models.Model):
    _name = 'fleet.flow.fuel.expense'
    _inherit = ['mail.thread']
    _description = 'FleetFlow Fuel & Expense'
    _rec_name = 'display_name_custom'
    _order = 'date desc, id desc'

    vehicle_id = fields.Many2one(
        'fleet.flow.vehicle',
        string='Vehicle',
        required=True,
        tracking=True,
    )
    trip_id = fields.Many2one(
        'fleet.flow.trip',
        string='Trip',
        tracking=True,
        help='Optional link to a specific trip',
    )
    expense_type = fields.Selection(
        selection=[
            ('fuel', 'Fuel'),
            ('toll', 'Toll'),
            ('parking', 'Parking'),
            ('other', 'Other'),
        ],
        string='Expense Type',
        required=True,
        default='fuel',
        tracking=True,
    )
    amount = fields.Float(
        string='Amount',
        required=True,
        tracking=True,
    )
    liters = fields.Float(
        string='Liters',
        help='Fuel quantity — used for fuel efficiency computation',
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        required=True,
    )
    odometer_at_fill = fields.Float(
        string='Odometer at Fill (km)',
    )
    notes = fields.Text(string='Notes')

    display_name_custom = fields.Char(
        string='Display Name', compute='_compute_display_name_custom',
    )

    vehicle_name = fields.Char(
        related='vehicle_id.name',
        string='Vehicle Name',
        store=True,
    )
    driver_id = fields.Many2one(
        related='trip_id.driver_id',
        string='Driver',
        store=True,
    )

    @api.onchange('trip_id')
    def _onchange_trip_id(self):
        if self.trip_id and self.trip_id.vehicle_id:
            self.vehicle_id = self.trip_id.vehicle_id

    @api.depends('vehicle_id.name', 'expense_type', 'date')
    def _compute_display_name_custom(self):
        for rec in self:
            vehicle = rec.vehicle_id.name or 'N/A'
            etype = dict(rec._fields['expense_type'].selection).get(rec.expense_type, '')
            rec.display_name_custom = f"{vehicle} - {etype} ({rec.date})" if rec.date else f"{vehicle} - {etype}"
