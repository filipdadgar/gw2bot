from src.core.discovery.route_builder import RouteBuilder
from src.core.persistence.storage import Storage


def test_route_discovery_scoring_increases_with_segments_and_nodes(tmp_path) -> None:
    storage = Storage(str(tmp_path / "data"))
    builder = RouteBuilder(storage)

    low = builder.score_loop(sampled_segments=3, encountered_nodes=1)
    high = builder.score_loop(sampled_segments=10, encountered_nodes=5)

    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0
    assert high > low
