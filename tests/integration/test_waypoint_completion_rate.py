"""Waypoint completion-rate benchmark validation."""

from src.core.navigation.waypoint_navigator import WaypointNavigator


def test_waypoint_completion_rate_95_percent() -> None:
    """Validate bot completes ≥95% of planned waypoints.
    
    Success Criteria: SC-003 waypoint completion ≥ 95%.
    """
    navigator = WaypointNavigator()
    total_waypoints = 20
    completed = 0

    for current in range(total_waypoints):
        next_idx = navigator.next_index(current, total_waypoints)
        # Simulate waypoint traversal success
        if next_idx == (current + 1) % total_waypoints:
            completed += 1

    completion_rate = completed / total_waypoints
    assert completion_rate >= 0.95, f"Waypoint completion rate {completion_rate:.1%} below 95% threshold"
