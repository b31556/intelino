import pathlib
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "real"))
sys.path.insert(0, str(ROOT / "tests"))

try:
    import intelino.trainlib  # noqa: F401  the real library, when it is installed
except ImportError:
    # control.py only needs these names, so the tests run without the library or any train
    intelino = types.ModuleType("intelino")
    trainlib = types.ModuleType("intelino.trainlib")
    enums = types.ModuleType("intelino.trainlib.enums")
    trainlib.TrainScanner = type("TrainScanner", (), {})
    trainlib.Train = type("Train", (), {})
    enums.SnapColorValue = type("SnapColorValue", (), dict(WHITE="WHITE", MAGENTA="MAGENTA", BLACK="BLACK", CYAN="CYAN"))
    enums.SteeringDecision = type("SteeringDecision", (), dict(LEFT="LEFT", RIGHT="RIGHT"))
    enums.MovementDirection = type("MovementDirection", (), dict(FORWARD="FORWARD", BACKWARD="BACKWARD", INVERT="INVERT"))
    intelino.trainlib, trainlib.enums = trainlib, enums
    sys.modules.update({"intelino": intelino, "intelino.trainlib": trainlib, "intelino.trainlib.enums": enums})


@pytest.fixture(autouse=True)
def repo_cwd(monkeypatch):
    monkeypatch.chdir(ROOT)  # navigate.py reads real/map.json relative to the working directory
