"""FastAPI application factory and baseline runtime wiring."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import threading
import time

from fastapi import FastAPI

from src.adapters.bridge_factory import get_bridges
from src.api.routes.discovery import router as discovery_router
from src.api.routes.run import router as run_router
from src.api.routes.run_control import router as run_control_router
from src.api.routes.telemetry import router as telemetry_router
from src.api.routes.training import router as training_router
from src.config.settings import get_settings
from src.core.discovery.route_builder import RouteBuilder
from src.core.orchestration.control_commands import ControlCommands
from src.core.orchestration.discovery_orchestrator import DiscoveryOrchestrator
from src.core.orchestration.farm_cycle_orchestrator import FarmCycleOrchestrator
from src.core.orchestration.policy_signal_emitter import PolicySignalEmitter
from src.core.persistence.policy_signal_store import PolicySignalStore
from src.core.persistence.storage import Storage
from src.core.training.demonstration_recorder import DemonstrationRecorder
from src.core.training.manual_input_listener import ManualInputListener
from src.core.training.policy_registry import PolicyRegistry
from src.telemetry.cycle_summary_service import CycleSummaryService
from src.telemetry.event_writer import EventWriter
from src.telemetry.logger import configure_logging

logger = logging.getLogger(__name__)


def _start_auto_retrain_worker(policy_registry: PolicyRegistry, interval_seconds: int) -> None:
    """Start a daemon worker that retrains policy artifacts at fixed intervals."""

    def _worker() -> None:
        while True:
            try:
                policy_registry.train_latest()
            except ValueError as exc:
                if str(exc) != "no_policy_samples":
                    logger.exception("auto_retrain_failed")
            except Exception:
                logger.exception("auto_retrain_failed")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_worker, name="gw2bot-auto-retrain", daemon=True)
    thread.start()


def _startup_autostart_run(app: FastAPI) -> None:
    if not bool(app.state.settings.gw2_autostart_run_enabled):
        return

    orchestrator = app.state.farm_cycle_orchestrator
    snapshot = orchestrator.start(route_id=None, auto_discover_if_missing=True)
    if snapshot.status != "running":
        logger.warning("Mission autostart requested but run could not start: %s", snapshot.last_error)
        return

    settings = app.state.settings
    interval_seconds = max(0.05, float(settings.gw2_runtime_signal_interval_ms) / 1000.0)
    capture_bridge = app.state.capture_bridge if bool(app.state.bridge_enabled) else None
    orchestrator.start_runtime_loop(
        capture_bridge=capture_bridge,
        policy_registry=app.state.policy_registry,
        policy_enabled=bool(settings.gw2_runtime_policy_enabled),
        policy_min_confidence=float(settings.gw2_runtime_policy_min_confidence),
        interval_seconds=interval_seconds,
    )

    if capture_bridge is None:
        orchestrator.seed_policy_signals()

    logger.info("Mission mode autostart enabled: run started automatically")


def create_app() -> FastAPI:
    """Create the API app used by local runtime control endpoints."""

    settings = get_settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _startup_autostart_run(app)
        yield

    app = FastAPI(title="GW2 Bot Control API", version="0.1.0", lifespan=lifespan)

    # Initialize host bridges for screen capture and input automation
    try:
        capture_bridge, input_bridge = get_bridges(window_title="Guild Wars 2")
        logger.info("✅ Host bridges initialized successfully")
        bridge_enabled = True
    except Exception as e:
        logger.warning(f"⚠️ Host bridge initialization failed: {e}")
        logger.info("Bot will run in simulation mode without real capture/input")
        capture_bridge = None
        input_bridge = None
        bridge_enabled = False

    try:
        storage = Storage(settings.gw2_data_dir)
    except OSError as exc:
        logger.warning("Failed to initialize storage at %s: %s", settings.gw2_data_dir, exc)
        logger.warning("Falling back to local data directory")
        storage = Storage("data")
    route_builder = RouteBuilder(storage)
    discovery_orchestrator = DiscoveryOrchestrator(route_builder)
    farm_cycle_orchestrator = FarmCycleOrchestrator(storage, discovery_orchestrator)
    event_writer = EventWriter(storage)
    cycle_summary_service = CycleSummaryService(storage)
    control_commands = ControlCommands(farm_cycle_orchestrator)
    policy_registry = PolicyRegistry(storage)
    demo_recorder = DemonstrationRecorder(
        signal_store=PolicySignalStore(storage),
        signal_emitter=PolicySignalEmitter(),
        capture_bridge=capture_bridge,
        bridge_enabled=bridge_enabled,
    )
    manual_input_listener = ManualInputListener(demo_recorder)

    if settings.gw2_training_auto_retrain_enabled:
        interval = max(1, settings.gw2_training_retrain_interval_seconds)
        _start_auto_retrain_worker(policy_registry=policy_registry, interval_seconds=interval)
        logger.info("Auto-retrain worker enabled (interval=%ss)", interval)

    # Store in app state
    app.state.storage = storage
    app.state.settings = settings
    app.state.route_builder = route_builder
    app.state.discovery_orchestrator = discovery_orchestrator
    app.state.farm_cycle_orchestrator = farm_cycle_orchestrator
    app.state.event_writer = event_writer
    app.state.cycle_summary_service = cycle_summary_service
    app.state.control_commands = control_commands
    app.state.policy_registry = policy_registry
    app.state.demonstration_recorder = demo_recorder
    app.state.manual_input_listener = manual_input_listener
    app.state.capture_bridge = capture_bridge
    app.state.input_bridge = input_bridge
    app.state.bridge_enabled = bridge_enabled

    app.include_router(discovery_router)
    app.include_router(run_router)
    app.include_router(run_control_router)
    app.include_router(telemetry_router)
    app.include_router(training_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "host_bridge": "enabled" if bridge_enabled else "disabled",
        }

    return app


app = create_app()
