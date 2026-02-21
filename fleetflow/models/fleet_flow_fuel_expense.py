from odoo import fields, models


class FleetFlowFuelExpense(models.Model):
    _name = 'fleet.flow.fuel.expense'
    _inherit = ['mail.thread']
    _description = 'FleetFlow Fuel & Expense'
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
