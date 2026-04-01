"""Manual demonstration recorder for behavior-cloning style data capture."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import numpy as np

from src.adapters.bridge_interfaces import CaptureBridge
from src.core.orchestration.policy_signal_emitter import PolicySignalEmitter
from src.core.persistence.policy_signal_store import PolicySignalStore


@dataclass
class DemoSession:
    session_id: str
    step_index: int
    active: bool


class DemonstrationRecorder:
    """Records operator-labeled actions as policy signals for training."""

    def __init__(
        self,
        signal_store: PolicySignalStore,
        signal_emitter: PolicySignalEmitter,
        capture_bridge: CaptureBridge | None,
        bridge_enabled: bool,
    ) -> None:
        self._store = signal_store
        self._emitter = signal_emitter
        self._capture_bridge = capture_bridge
        self._bridge_enabled = bridge_enabled
        self._lock = threading.Lock()
        self._session: DemoSession | None = None

    def start(self) -> DemoSession:
        with self._lock:
            self._session = DemoSession(session_id=f"demo-{uuid4().hex[:8]}", step_index=0, active=True)
            return self._session

    def status(self) -> DemoSession | None:
        with self._lock:
            return self._session

    def stop(self) -> DemoSession | None:
        with self._lock:
            if self._session is None:
                return None
            self._session.active = False
            ended = self._session
            self._session = None
            return ended

    def record(
        self,
        action_taken: str,
        reward_proxy: float,
        terminal: bool,
        state_features: dict[str, object] | None = None,
    ) -> dict[str, object]:
        with self._lock:
            if self._session is None or not self._session.active:
                # Auto-start a persistent session so manual keypresses are always
                # captured without requiring an explicit API call to start recording.
                self._session = DemoSession(
                    session_id=f"demo-{uuid4().hex[:8]}",
                    step_index=0,
                    active=True,
                )

            session = self._session
            features = state_features or self._capture_state_features()
            features["source"] = "manual_demo"

            signal = self._emitter.emit(
                cycle_id=session.session_id,
                step_index=session.step_index,
                state_features=features,
                action_taken=action_taken,
                reward_proxy=reward_proxy,
                terminal=terminal,
                observation_ref=None,
            )
            self._store.persist(signal)
            session.step_index += 1
            return signal

    def _capture_state_features(self) -> dict[str, object]:
        if self._bridge_enabled and self._capture_bridge is not None:
            try:
                frame_capture = self._capture_bridge.capture()
                frame = frame_capture.frame
                brightness = float(np.mean(frame) / 255.0)
                contrast = float(np.std(frame) / 255.0)
                return {
                    "brightness": round(brightness, 4),
                    "contrast": round(contrast, 4),
                    "frame_width": frame_capture.width,
                    "frame_height": frame_capture.height,
                    "bridge_enabled": 1.0,
                }
            except Exception:
                pass

        return {
            "brightness": 0.5,
            "contrast": 0.25,
            "frame_width": 0,
            "frame_height": 0,
            "bridge_enabled": 0.0,
        }
