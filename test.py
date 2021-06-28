import pickle

import mission_control


mission_control.connect()

project, _ = mission_control.Project.get_or_create(
    name="test-project",
    metadata={
        "test1": "hi",
        "test2": [{"nested1": "a", "nested2": ["b", "c"]}, {"nested1": "d"}],
    },
)

experiment = project.get_experiment(name="Test experiment", metadata={"foo": "bar"})

for i in range(2):
    run = experiment.get_run(name=f"run{i}", metadata={"seed": i})
    for j in range(10):
        run.write_log(
            log_data={"step": j, "loss": (i + 1) * j},
            binary_data=pickle.dumps(["hi", 1, 7, {"wow": "hello"}]),
        )
