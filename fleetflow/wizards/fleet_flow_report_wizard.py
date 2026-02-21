# -*- coding: utf-8 -*-
# Part of FleetFlow. See LICENSE file for full copyright and licensing details.

import base64
import csv
import io
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FleetFlowReportWizard(models.TransientModel):
    _name = 'fleet.flow.report.wizard'
    _description = 'FleetFlow Report Export Wizard'

    report_type = fields.Selection(
        selection=[
            ('fuel_expense', 'Fuel & Expense Report'),
            ('trip_summary', 'Trip Summary Report'),
            ('driver_performance', 'Driver Performance Report'),
            ('vehicle_roi', 'Vehicle ROI Report'),
        ],
        string='Report Type',
        required=True,
        default='fuel_expense',
    )
    date_from = fields.Date(
        string='Date From',
        default=lambda self: date.today().replace(day=1),
    )
    date_to = fields.Date(
        string='Date To',
        default=fields.Date.context_today,
    )
    vehicle_id = fields.Many2one(
        'fleet.flow.vehicle',
        string='Vehicle',
        help='Leave empty for all vehicles',
    )
    driver_id = fields.Many2one(
        'fleet.flow.driver',
        string='Driver',
        help='Leave empty for all drivers',
    )

    csv_file = fields.Binary(string='CSV File', readonly=True, attachment=False)
    csv_filename = fields.Char(string='Filename', readonly=True)

    def _fmt_date(self, d):
        """Return date as dd-mm-yyyy string (plain text in Excel, no ### issue)."""
        if not d:
            return ''
        if isinstance(d, str):
            from datetime import datetime
            d = datetime.strptime(d, '%Y-%m-%d').date()
        return d.strftime('%d-%m-%Y')

    def action_generate_report(self):
        self.ensure_one()
        method_name = f'_generate_{self.report_type}'
        if not hasattr(self, method_name):
            raise UserError(_('Invalid report type selected.'))

        headers, rows = getattr(self, method_name)()

        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        csv_content = output.getvalue().encode('utf-8')

        filename = f'fleetflow_{self.report_type}_{date.today().strftime("%d-%m-%Y")}.csv'

        self.write({
            'csv_file': base64.b64encode(csv_content),
            'csv_filename': filename,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=fleet.flow.report.wizard&id={self.id}'
                   f'&field=csv_file&filename={filename}&download=true',
            'target': 'self',
        }

    def _generate_fuel_expense(self):
        domain = []
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        if self.vehicle_id:
            domain.append(('vehicle_id', '=', self.vehicle_id.id))

        records = self.env['fleet.flow.fuel.expense'].search(domain, order='date asc')

        headers = ['Date', 'Vehicle', 'Expense Type', 'Amount', 'Liters', 'Trip', 'Notes']
        rows = []
        for rec in records:
            rows.append([
                self._fmt_date(rec.date),
                rec.vehicle_id.name if rec.vehicle_id else '',
                dict(rec._fields['expense_type'].selection).get(rec.expense_type, ''),
                rec.amount or 0.0,
                rec.liters or '',
                rec.trip_id.name if rec.trip_id else '',
                rec.notes or '',
            ])
        return headers, rows

    def _generate_trip_summary(self):
        domain = [('state', '=', 'completed')]
        if self.date_from:
            domain.append(('departure_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('departure_date', '<=', self.date_to))
        if self.vehicle_id:
            domain.append(('vehicle_id', '=', self.vehicle_id.id))
        if self.driver_id:
            domain.append(('driver_id', '=', self.driver_id.id))

        records = self.env['fleet.flow.trip'].search(domain, order='departure_date asc')

        headers = [
            'Trip Ref', 'Vehicle', 'Driver', 'Origin', 'Destination',
            'Distance (km)', 'Cargo (kg)', 'Revenue', 'Departure', 'Arrival',
        ]
        rows = []
        for rec in records:
            rows.append([
                rec.name,
                rec.vehicle_id.name if rec.vehicle_id else '',
                rec.driver_id.name if rec.driver_id else '',
                rec.origin or '',
                rec.destination or '',
                rec.distance or 0.0,
                rec.cargo_weight or 0.0,
                rec.revenue or 0.0,
                self._fmt_date(rec.departure_date),
                self._fmt_date(rec.arrival_date),
            ])
        return headers, rows

    def _generate_driver_performance(self):
        domain = []
        if self.driver_id:
            domain.append(('id', '=', self.driver_id.id))

        drivers = self.env['fleet.flow.driver'].search(domain, order='name asc')

        headers = [
            'Driver', 'License Category', 'License Expiry', 'License Status',
            'Safety Score', 'Status', 'Total Trips', 'Completed Trips',
        ]
        rows = []
        for drv in drivers:
            completed = self.env['fleet.flow.trip'].search_count([
                ('driver_id', '=', drv.id),
                ('state', '=', 'completed'),
            ])
            total = self.env['fleet.flow.trip'].search_count([
                ('driver_id', '=', drv.id),
            ])
            rows.append([
                drv.name,
                dict(drv._fields['license_category'].selection).get(drv.license_category, ''),
                self._fmt_date(drv.license_expiry),
                'Expired' if drv.is_license_expired else f'{drv.license_days_remaining} days remaining',
                drv.safety_score or 0.0,
                dict(drv._fields['status'].selection).get(drv.status, ''),
                total,
                completed,
            ])
        return headers, rows

    def _generate_vehicle_roi(self):
        domain = []
        if self.vehicle_id:
            domain.append(('id', '=', self.vehicle_id.id))

        vehicles = self.env['fleet.flow.vehicle'].search(domain, order='name asc')

        headers = [
            'Vehicle', 'License Plate', 'Type', 'Status',
            'Acquisition Cost', 'Total Revenue', 'Total Fuel Cost',
            'Total Maintenance Cost', 'ROI (%)', 'Total Distance (km)',
            'Cost per km', 'Fuel Efficiency (km/L)',
        ]
        rows = []
        for veh in vehicles:
            rows.append([
                veh.name,
                veh.license_plate or '',
                dict(veh._fields['vehicle_type'].selection).get(veh.vehicle_type, ''),
                dict(veh._fields['status'].selection).get(veh.status, ''),
                veh.acquisition_cost or 0.0,
                veh.total_revenue or 0.0,
                veh.total_fuel_cost or 0.0,
                veh.total_maintenance_cost or 0.0,
                round(veh.roi or 0.0, 2),
                veh.total_distance or 0.0,
                round(veh.cost_per_km or 0.0, 2),
                round(veh.fuel_efficiency or 0.0, 2),
            ])
        return headers, rows