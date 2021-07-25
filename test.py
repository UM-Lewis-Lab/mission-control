from pathlib import Path
from random import random
from mission_control import MissionControl


mc = MissionControl(
    "test-project",
    "test-experiment",
    "test-run",
    Path("~/Downloads/mc-root"),
    ["step", "loss"],
    project_metadata={"test": "project", "hi": "wow", "hello": ["hi"]},
    experiment_metadata={"test": "experiment"},
    run_metadata={"test": "run"},
    backup_logs=True,
    backup_artifacts=True,
    overwrite=True,
)

for i in range(12):
    mc.save_log(step=i, loss=random())

mc.save_artifact({"hello": "world!"}, "test-artifact", {"some-test": "metadata"})
mc.save_artifact({"hello": "world!"}, "test-artifact", {"some-test": "metadata2"})
mc.save_artifact({"hello": "world!"}, "test-artifact2", {"2some-test": "metadata"})

mc.finish()
