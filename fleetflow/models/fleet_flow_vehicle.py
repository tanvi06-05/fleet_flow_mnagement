from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FleetFlowVehicle(models.Model):
    _name = 'fleet.flow.vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'FleetFlow Vehicle'
    _rec_name = 'name'
    _order = 'license_plate asc'
    _license_plate_unique = models.Constraint(
        'UNIQUE(license_plate)',
        'License plate must be unique!',
    )

    name = fields.Char(
        string='Vehicle Name / Model',
        required=True,
        tracking=True,
        help='Free-text vehicle name or model (e.g., "Van-05", "Mercedes Sprinter")',
    )
    license_plate = fields.Char(
        string='License Plate',
        required=True,
        tracking=True,
        help='Unique identifier — SQL unique constraint enforced at database level',
    )
    vehicle_type = fields.Selection(
        selection=[
            ('truck', 'Truck'),
            ('van', 'Van'),
            ('bike', 'Bike'),
        ],
        string='Vehicle Type',
        required=True,
        default='van',
        tracking=True,
        help='Links to driver license category validation',
    )
    max_load_capacity = fields.Float(
        string='Max Load Capacity (kg)',
        help='In kilograms — used by cargo weight validation constraint on trips',
    )
    odometer = fields.Float(
        string='Odometer (km)',
        tracking=True,
        help='Current km reading — updated automatically on trip completion',
    )
    acquisition_cost = fields.Float(
        string='Acquisition Cost',
        tracking=True,
        help='Used to compute Vehicle ROI automatically',
    )
    region = fields.Char(
        string='Region / Location',
        help='Filterable field for regional fleet management',
    )
    out_of_service = fields.Boolean(
        string='Out of Service',
        default=False,
        tracking=True,
        help='Boolean toggle that switches status to Retired; reversible by manager',
    )
    status = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('on_trip', 'On Trip'),
            ('in_shop', 'In Shop'),
            ('retired', 'Retired'),
        ],
        string='Status',
        default='available',
        required=True,
        tracking=True,
    )
    image = fields.Binary(string='Image')
    notes = fields.Html(string='Notes')
    active = fields.Boolean(default=True)

    trip_ids = fields.One2many(
        'fleet.flow.trip', 'vehicle_id', string='Trips',
    )
    maintenance_ids = fields.One2many(
        'fleet.flow.maintenance', 'vehicle_id', string='Maintenance Logs',
    )
    fuel_expense_ids = fields.One2many(
        'fleet.flow.fuel.expense', 'vehicle_id', string='Fuel & Expenses',
    )

    trip_count = fields.Integer(
        string='Trip Count', compute='_compute_counts',
    )
    maintenance_count = fields.Integer(
        string='Maintenance Count', compute='_compute_counts',
    )
    expense_count = fields.Integer(
        string='Expense Count', compute='_compute_counts',
    )
    total_fuel_cost = fields.Float(
        string='Total Fuel Cost', compute='_compute_financials', store=True,
    )
    total_maintenance_cost = fields.Float(
        string='Total Maintenance Cost', compute='_compute_financials', store=True,
    )
    total_revenue = fields.Float(
        string='Total Revenue', compute='_compute_financials', store=True,
    )
    roi = fields.Float(
        string='ROI (%)', compute='_compute_financials', store=True,
    )
    cost_per_km = fields.Float(
        string='Cost per km', compute='_compute_efficiency', store=True,
    )
    fuel_efficiency = fields.Float(
        string='Fuel Efficiency (km/L)', compute='_compute_efficiency', store=True,
    )
    total_distance = fields.Float(
        string='Total Distance (km)', compute='_compute_efficiency', store=True,
    )

    @api.depends('trip_ids', 'maintenance_ids', 'fuel_expense_ids')
    def _compute_counts(self):
        for rec in self:
            rec.trip_count = len(rec.trip_ids)
            rec.maintenance_count = len(rec.maintenance_ids)
            rec.expense_count = len(rec.fuel_expense_ids)

    @api.depends(
        'fuel_expense_ids.amount',
        'maintenance_ids.cost',
        'maintenance_ids.state',
        'trip_ids.revenue',
        'trip_ids.state',
        'acquisition_cost',
    )
    def _compute_financials(self):
        for rec in self:
            rec.total_fuel_cost = sum(rec.fuel_expense_ids.mapped('amount'))
            rec.total_maintenance_cost = sum(
                rec.maintenance_ids.filtered(
                    lambda m: m.state == 'completed'
                ).mapped('cost')
            )
            rec.total_revenue = sum(
                rec.trip_ids.filtered(
                    lambda t: t.state == 'completed'
                ).mapped('revenue')
            )
            total_cost = rec.total_fuel_cost + rec.total_maintenance_cost
            if rec.acquisition_cost:
                rec.roi = (
                    (rec.total_revenue - total_cost)
                    / rec.acquisition_cost
                ) * 100
            else:
                rec.roi = 0.0

    @api.depends(
        'trip_ids.distance',
        'trip_ids.state',
        'fuel_expense_ids.amount',
        'fuel_expense_ids.liters',
    )
    def _compute_efficiency(self):
        for rec in self:
            completed_trips = rec.trip_ids.filtered(lambda t: t.state == 'completed')
            rec.total_distance = sum(completed_trips.mapped('distance'))
            total_cost = sum(rec.fuel_expense_ids.mapped('amount')) + sum(
                rec.maintenance_ids.filtered(lambda m: m.state == 'completed').mapped('cost')
            )
            rec.cost_per_km = total_cost / rec.total_distance if rec.total_distance else 0.0
            total_liters = sum(rec.fuel_expense_ids.mapped('liters'))
            rec.fuel_efficiency = rec.total_distance / total_liters if total_liters else 0.0

    @api.onchange('out_of_service')
    def _onchange_out_of_service(self):
        if self.out_of_service:
            self.status = 'retired'
        elif self.status == 'retired':
            self.status = 'available'

    def action_retire(self):
        for rec in self:
            rec.write({'status': 'retired', 'out_of_service': True})

    def action_reactivate(self):
        for rec in self:
            rec.write({'status': 'available', 'out_of_service': False})

    def action_view_trips(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Trips'),
            'res_model': 'fleet.flow.trip',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Maintenance'),
            'res_model': 'fleet.flow.maintenance',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }

    def action_view_expenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Fuel & Expenses'),
            'res_model': 'fleet.flow.fuel.expense',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }