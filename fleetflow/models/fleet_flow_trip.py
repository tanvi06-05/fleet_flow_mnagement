from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FleetFlowTrip(models.Model):
    _name = 'fleet.flow.trip'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'FleetFlow Trip'
    _rec_name = 'name'
    _order = 'name desc'

    name = fields.Char(
        string='Trip Reference',
        readonly=True,
        default=lambda self: _('New'),
        copy=False,
    )
    vehicle_id = fields.Many2one(
        'fleet.flow.vehicle',
        string='Vehicle',
        required=True,
        tracking=True,
    )
    driver_id = fields.Many2one(
        'fleet.flow.driver',
        string='Driver',
        required=True,
        tracking=True,
    )
    origin = fields.Char(string='Origin', required=True)
    destination = fields.Char(string='Destination', required=True)
    distance = fields.Float(string='Distance (km)')
    cargo_weight = fields.Float(
        string='Cargo Weight (kg)',
        help='Must not exceed vehicle max load capacity',
    )
    revenue = fields.Float(string='Revenue', tracking=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('dispatched', 'Dispatched'),
            ('on_trip', 'On Trip'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    departure_date = fields.Datetime(string='Departure Date')
    arrival_date = fields.Datetime(string='Arrival Date')
    odometer_start = fields.Float(string='Odometer Start (km)')
    odometer_end = fields.Float(string='Odometer End (km)')
    notes = fields.Html(string='Notes')

    fuel_expense_ids = fields.One2many(
        'fleet.flow.fuel.expense', 'trip_id', string='Fuel & Expenses',
    )

    vehicle_type = fields.Selection(
        related='vehicle_id.vehicle_type', string='Vehicle Type', store=True,
    )
    max_load = fields.Float(
        related='vehicle_id.max_load_capacity', string='Max Load (kg)',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'fleet.flow.trip'
                ) or _('New')
        return super().create(vals_list)

    @api.constrains('cargo_weight', 'vehicle_id')
    def _check_cargo_weight(self):
        for rec in self:
            if (
                rec.cargo_weight
                and rec.vehicle_id
                and rec.vehicle_id.max_load_capacity
                and rec.cargo_weight > rec.vehicle_id.max_load_capacity
            ):
                raise ValidationError(
                    _(
                        'Cargo weight (%(weight)s kg) exceeds vehicle '
                        'max load capacity (%(max)s kg)!',
                        weight=rec.cargo_weight,
                        max=rec.vehicle_id.max_load_capacity,
                    )
                )

    @api.constrains('driver_id', 'vehicle_id')
    def _check_driver_license_category(self):
        for rec in self:
            if (
                rec.driver_id
                and rec.vehicle_id
                and rec.driver_id.license_category != rec.vehicle_id.vehicle_type
            ):
                raise ValidationError(
                    _(
                        'Driver license category "%(cat)s" does not match '
                        'vehicle type "%(vtype)s"!',
                        cat=rec.driver_id.license_category,
                        vtype=rec.vehicle_id.vehicle_type,
                    )
                )

    def action_dispatch(self):
        for rec in self:
            if rec.driver_id.is_license_expired:
                raise ValidationError(
                    _('Cannot dispatch: driver license is expired!')
                )
            rec.state = 'dispatched'
            rec.vehicle_id.status = 'on_trip'
            rec.driver_id.status = 'on_trip'

    def action_start(self):
        for rec in self:
            rec.state = 'on_trip'
            rec.odometer_start = rec.vehicle_id.odometer

    def action_complete(self):
        for rec in self:
            rec.state = 'completed'
            rec.arrival_date = fields.Datetime.now()
            if rec.odometer_end:
                rec.vehicle_id.odometer = rec.odometer_end
                rec.distance = rec.odometer_end - rec.odometer_start
            rec.vehicle_id.status = 'available'
            rec.driver_id.status = 'on_duty'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
            if rec.vehicle_id.status == 'on_trip':
                rec.vehicle_id.status = 'available'
            if rec.driver_id.status == 'on_trip':
                rec.driver_id.status = 'on_duty'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'
