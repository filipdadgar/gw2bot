"""FastAPI application factory and baseline runtime wiring."""

from __future__ import annotations

from fastapi import FastAPI

from src.api.routes.discovery import router as discovery_router
from src.api.routes.run import router as run_router
from src.api.routes.run_control import router as run_control_router
from src.api.routes.telemetry import router as telemetry_router
from src.config.settings import get_settings
from src.core.discovery.route_builder import RouteBuilder
from src.core.orchestration.control_commands import ControlCommands
from src.core.orchestration.discovery_orchestrator import DiscoveryOrchestrator
from src.core.orchestration.farm_cycle_orchestrator import FarmCycleOrchestrator
from src.core.persistence.storage import Storage
from src.telemetry.cycle_summary_service import CycleSummaryService
from src.telemetry.event_writer import EventWriter
from src.telemetry.logger import configure_logging


def create_app() -> FastAPI:
    """Create the API app used by local runtime control endpoints."""

    settings = get_settings()
    configure_logging()

    app = FastAPI(title="GW2 Bot Control API", version="0.1.0")

    storage = Storage(settings.gw2_data_dir)
    route_builder = RouteBuilder(storage)
    discovery_orchestrator = DiscoveryOrchestrator(route_builder)
    farm_cycle_orchestrator = FarmCycleOrchestrator(storage, discovery_orchestrator)
    event_writer = EventWriter(storage)
    cycle_summary_service = CycleSummaryService(storage)
    control_commands = ControlCommands(farm_cycle_orchestrator)

    app.state.storage = storage
    app.state.route_builder = route_builder
    app.state.discovery_orchestrator = discovery_orchestrator
    app.state.farm_cycle_orchestrator = farm_cycle_orchestrator
    app.state.event_writer = event_writer
    app.state.cycle_summary_service = cycle_summary_service
    app.state.control_commands = control_commands

    app.include_router(discovery_router)
    app.include_router(run_router)
    app.include_router(run_control_router)
    app.include_router(telemetry_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "host_bridge": "enabled" if settings.gw2_host_bridge_enabled else "disabled",
        }

    return app


app = create_app()
