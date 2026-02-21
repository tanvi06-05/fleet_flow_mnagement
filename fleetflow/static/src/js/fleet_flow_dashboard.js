/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

class FleetFlowDashboard extends Component {
    static template = "fleetflow.Dashboard";
    static props = { ...standardActionServiceProps };

    setup() {
        this.action = useService("action");
        this.state = useState({
            vehicles: {},
            drivers: {},
            trips: {},
            maintenance: {},
            kpis: {},
            isLoading: true,
        });

        onWillStart(async () => {
            await this._fetchDashboardData();
        });
    }

    async _fetchDashboardData() {
        this.state.isLoading = true;
        const data = await rpc("/fleetflow/dashboard/data", {});
        Object.assign(this.state, data, { isLoading: false });
    }

    async refresh() {
        await this._fetchDashboardData();
    }

    // ---- Navigation helpers ----
    openActiveFleet() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Active Fleet (On Trip)",
            res_model: "fleet.flow.vehicle",
            view_mode: "kanban,list,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [["status", "=", "on_trip"]],
        });
    }

    openMaintenanceAlerts() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Vehicles In Shop",
            res_model: "fleet.flow.vehicle",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: [["status", "=", "in_shop"]],
        });
    }

    openPendingCargo() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Pending Cargo",
            res_model: "fleet.flow.trip",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "=", "draft"]],
        });
    }

    openAllVehicles() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "All Vehicles",
            res_model: "fleet.flow.vehicle",
            view_mode: "kanban,list,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
        });
    }

    openAvailableVehicles() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Available Vehicles",
            res_model: "fleet.flow.vehicle",
            view_mode: "kanban,list,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [["status", "=", "available"]],
        });
    }

    openActiveTrips() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Active Trips",
            res_model: "fleet.flow.trip",
            view_mode: "kanban,list,form",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            domain: [["state", "in", ["dispatched", "on_trip"]]],
        });
    }

    openCompletedTrips() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Completed Trips",
            res_model: "fleet.flow.trip",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "=", "completed"]],
        });
    }

    openAllDrivers() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Drivers",
            res_model: "fleet.flow.driver",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
        });
    }

    openExpiredLicenses() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Expired Licenses",
            res_model: "fleet.flow.driver",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: [["is_license_expired", "=", true]],
        });
    }

    openExpiringSoon() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "License Expiring Soon",
            res_model: "fleet.flow.driver",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: [["is_license_expired", "=", false], ["license_days_remaining", "<=", 30]],
        });
    }

    openPendingMaintenance() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Pending Maintenance",
            res_model: "fleet.flow.maintenance",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "in", ["planned", "in_progress"]]],
        });
    }
}

registry.category("actions").add("fleetflow_dashboard", FleetFlowDashboard);
