# -*- coding: utf-8 -*-
# Part of FleetFlow. See LICENSE file for full copyright and licensing details.
{
    'name': 'FleetFlow',
    'version': '19.0.1.0.0',
    'sequence': 190,
    'category': 'Human Resources/Fleet',
    'summary': 'Modular Fleet & Logistics Management System',
    'description': """
FleetFlow — Fleet & Logistics Management
=========================================
Comprehensive fleet management with vehicle registry, driver compliance,
trip dispatch, maintenance tracking, fuel/expense logging, analytics
dashboards, and CSV report export.

Main Features
-------------
* Vehicle Registry with status management and ROI computation
* Driver Profiles with license compliance and safety scoring
* Trip Dispatch lifecycle (Draft → Dispatched → On Trip → Completed)
* Maintenance Logs with auto vehicle status management
* Fuel & Expense Tracking per vehicle/trip
* Analytics (Pivot, Graph) for vehicles, trips, and expenses
* CSV Report Wizard with 4 report types
* 4 RBAC Security Roles
    """,
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/fleet_flow_groups.xml',
        'security/ir.model.access.csv',
        'data/fleet_flow_data.xml',
        'views/fleet_flow_vehicle_views.xml',
        'views/fleet_flow_driver_views.xml',
        'views/fleet_flow_trip_views.xml',
        'views/fleet_flow_maintenance_views.xml',
        'views/fleet_flow_fuel_expense_views.xml',
        'views/fleet_flow_analytics_views.xml',
        'views/fleet_flow_dashboard_views.xml',
        'wizards/fleet_flow_report_wizard_views.xml',
        'views/fleet_flow_menu.xml',
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'fleetflow/static/src/css/fleetflow.css',
            'fleetflow/static/src/js/fleet_flow_dashboard.js',
            'fleetflow/static/src/xml/fleet_flow_dashboard.xml',
        ],
    },
    'author': 'FleetFlow',
    'license': 'LGPL-3',
}
