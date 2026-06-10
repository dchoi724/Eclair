import pytest
from pathlib import Path

from topping_bot.optimize.reader import extract_topping_data, extract_unique_frames
from topping_bot.optimize.toppings import INFO, Resonance, Type

MOCK_DIR = Path(__file__).parent / "mock"

_FLAVOR_BY_FILENAME = {v["filename"]: k for k, v in INFO.items()}
_RESONANCE_BY_STEM = {r.value.lower().replace(" ", "_"): r for r in Resonance}


def _scan(video_path: Path):
    toppings = list(extract_topping_data(extract_unique_frames(video_path)))
    assert toppings, f"No toppings extracted from {video_path.name}"
    return toppings[0]


@pytest.mark.parametrize("video", sorted((MOCK_DIR / "normal").glob("*.mp4")), ids=lambda p: p.stem)
def test_normal_flavor(video):
    topping = _scan(video)
    assert topping.resonance == Resonance.NORMAL, (
        f"{video.stem}: expected NORMAL, got {topping.resonance}"
    )
    assert topping.flavor == _FLAVOR_BY_FILENAME[video.stem], (
        f"{video.stem}: expected flavor {_FLAVOR_BY_FILENAME[video.stem]}, got {topping.flavor}"
    )


@pytest.mark.parametrize("video", sorted((MOCK_DIR / "resonant").glob("*.mp4")), ids=lambda p: p.stem)
def test_resonant_type(video):
    topping = _scan(video)
    assert topping.resonance == _RESONANCE_BY_STEM[video.stem], (
        f"{video.stem}: expected {_RESONANCE_BY_STEM[video.stem]}, got {topping.resonance}"
    )
