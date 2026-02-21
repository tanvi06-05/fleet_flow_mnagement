from odoo import http
from odoo.http import request


class FleetFlowDashboardController(http.Controller):

    @http.route('/fleetflow/dashboard/data', type='jsonrpc', auth='user')
    def get_dashboard_data(self):
        Vehicle = request.env['fleet.flow.vehicle']
        Driver = request.env['fleet.flow.driver']
        Trip = request.env['fleet.flow.trip']
        Maintenance = request.env['fleet.flow.maintenance']

        total_vehicles = Vehicle.search_count([])
        on_trip_vehicles = Vehicle.search_count([('status', '=', 'on_trip')])
        available_vehicles = Vehicle.search_count([('status', '=', 'available')])
        in_shop_vehicles = Vehicle.search_count([('status', '=', 'in_shop')])
        retired_vehicles = Vehicle.search_count([('status', '=', 'retired')])

        total_drivers = Driver.search_count([])
        on_trip_drivers = Driver.search_count([('status', '=', 'on_trip')])
        on_duty_drivers = Driver.search_count([('status', '=', 'on_duty')])
        suspended_drivers = Driver.search_count([('status', '=', 'suspended')])
        expired_licenses = Driver.search_count([('is_license_expired', '=', True)])
        expiring_soon = Driver.search_count([
            ('is_license_expired', '=', False),
            ('license_days_remaining', '<=', 30),
        ])

        draft_trips = Trip.search_count([('state', '=', 'draft')])
        active_trips = Trip.search_count([('state', 'in', ['dispatched', 'on_trip'])])
        completed_trips = Trip.search_count([('state', '=', 'completed')])

        pending_maintenance = Maintenance.search_count([
            ('state', 'in', ['planned', 'in_progress']),
        ])

        utilization_rate = (
            round(on_trip_vehicles / total_vehicles * 100, 1)
            if total_vehicles else 0
        )

        return {
            'vehicles': {
                'total': total_vehicles,
                'on_trip': on_trip_vehicles,
                'available': available_vehicles,
                'in_shop': in_shop_vehicles,
                'retired': retired_vehicles,
            },
            'drivers': {
                'total': total_drivers,
                'on_trip': on_trip_drivers,
                'on_duty': on_duty_drivers,
                'suspended': suspended_drivers,
                'expired_licenses': expired_licenses,
                'expiring_soon': expiring_soon,
            },
            'trips': {
                'draft': draft_trips,
                'active': active_trips,
                'completed': completed_trips,
            },
            'maintenance': {
                'pending': pending_maintenance,
            },
            'kpis': {
                'active_fleet': on_trip_vehicles,
                'utilization_rate': utilization_rate,
                'maintenance_alerts': in_shop_vehicles,
                'pending_cargo': draft_trips,
            },
        }
