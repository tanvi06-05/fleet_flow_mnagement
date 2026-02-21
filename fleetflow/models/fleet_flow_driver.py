from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class FleetFlowDriver(models.Model):
    _name = 'fleet.flow.driver'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'FleetFlow Driver'
    _rec_name = 'name'
    _order = 'name asc'

    name = fields.Char(
        string='Driver Name',
        required=True,
        tracking=True,
    )
    license_number = fields.Char(
        string='License Number',
        required=True,
        tracking=True,
    )
    license_category = fields.Selection(
        selection=[
            ('truck', 'Truck'),
            ('van', 'Van'),
            ('bike', 'Bike'),
        ],
        string='License Category',
        required=True,
        tracking=True,
        help='Must match the vehicle type for trip assignment',
    )
    license_expiry = fields.Date(
        string='License Expiry',
        required=True,
        tracking=True,
    )
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    safety_score = fields.Float(
        string='Safety Score',
        default=100.0,
        tracking=True,
        help='0-100 score, starts at 100. Decremented by incidents.',
    )
    status = fields.Selection(
        selection=[
            ('on_duty', 'On Duty'),
            ('on_trip', 'On Trip'),
            ('off_duty', 'Off Duty'),
            ('suspended', 'Suspended'),
        ],
        string='Status',
        default='on_duty',
        required=True,
        tracking=True,
    )
    image = fields.Binary(string='Photo')
    notes = fields.Html(string='Notes')
    active = fields.Boolean(default=True)

    is_license_expired = fields.Boolean(
        string='License Expired',
        compute='_compute_license_status',
        store=True,
    )
    license_days_remaining = fields.Integer(
        string='Days Until Expiry',
        compute='_compute_license_status',
        store=True,
    )

    trip_ids = fields.One2many(
        'fleet.flow.trip', 'driver_id', string='Trips',
    )
    trip_count = fields.Integer(
        string='Trip Count', compute='_compute_trip_stats',
    )
    completed_trip_count = fields.Integer(
        string='Completed Trips', compute='_compute_trip_stats',
    )
    completion_rate = fields.Float(
        string='Completion Rate (%)', compute='_compute_trip_stats',
        help='Percentage of completed trips out of total trips',
    )

    @api.depends('trip_ids', 'trip_ids.state')
    def _compute_trip_stats(self):
        for rec in self:
            rec.trip_count = len(rec.trip_ids)
            rec.completed_trip_count = len(
                rec.trip_ids.filtered(lambda t: t.state == 'completed')
            )
            rec.completion_rate = (
                (rec.completed_trip_count / rec.trip_count * 100)
                if rec.trip_count else 0.0
            )

    @api.depends('license_expiry')
    def _compute_license_status(self):
        today = date.today()
        for rec in self:
            if rec.license_expiry:
                delta = (rec.license_expiry - today).days
                rec.license_days_remaining = delta
                rec.is_license_expired = delta < 0
            else:
                rec.license_days_remaining = 0
                rec.is_license_expired = False

    @api.constrains('license_expiry')
    def _check_license_expiry(self):
        for rec in self:
            if rec.license_expiry and rec.license_expiry < date.today():
                pass

    @api.constrains('safety_score')
    def _check_safety_score(self):
        for rec in self:
            if rec.safety_score < 0 or rec.safety_score > 100:
                raise ValidationError(
                    _('Safety score must be between 0 and 100.')
                )

    def action_suspend(self):
        for rec in self:
            rec.status = 'suspended'

    def action_reactivate(self):
        for rec in self:
            rec.status = 'on_duty'

    def action_view_trips(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Trips'),
            'res_model': 'fleet.flow.trip',
            'view_mode': 'list,form',
            'domain': [('driver_id', '=', self.id)],
            'context': {'default_driver_id': self.id},
        }
