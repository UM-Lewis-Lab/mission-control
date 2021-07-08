from typing import Generator, Tuple
from uuid import uuid4

from peewee import ForeignKeyField, Model, CharField, SQL, UUIDField, BlobField
from playhouse.fields import PickleField
from playhouse.postgres_ext import BinaryJSONField, DateTimeField, PostgresqlExtDatabase

__all__ = ["postgres_db", "Project", "Experiment", "Run", "Log", "ALL_TABLES"]

postgres_db = PostgresqlExtDatabase(None)


def _split_kwargs(kwargs) -> Tuple[dict, dict]:
    """Splits uid into a separate dictionary. (Helper function for get_ methods)"""
    query = {"uid": kwargs.pop("uid")} if "uid" in kwargs else {}
    return query, kwargs


class BaseModel(Model):
    uid = UUIDField(primary_key=True, default=uuid4, index=True, null=False)
    created_at = DateTimeField(
        null=True, constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")]
    )

    class Meta:
        database = postgres_db


class Project(BaseModel):
    name = CharField(null=False, unique=True)
    metadata = BinaryJSONField(null=False, default=dict)

    class Meta:
        table_name = "projects"

    def get_experiment(self, **kwargs) -> "Experiment":
        query, kwargs = _split_kwargs(kwargs)
        kwargs["project"] = self
        return Experiment.get_or_create(**query, defaults=kwargs)[0]


class Experiment(BaseModel):
    name = CharField(null=False, unique=True)
    project = ForeignKeyField(
        Project, backref="experiments", null=False, on_delete="CASCADE"
    )
    metadata = BinaryJSONField(null=False, default=dict)

    class Meta:
        table_name = "experiments"

    def get_run(self, **kwargs) -> "Run":
        query, kwargs = _split_kwargs(kwargs)
        kwargs["experiment"] = self
        return Run.get_or_create(**query, defaults=kwargs)[0]


class Run(BaseModel):
    name = CharField(null=False, unique=True)
    experiment = ForeignKeyField(
        Experiment, backref="runs", null=False, on_delete="CASCADE"
    )
    metadata = BinaryJSONField(null=False, default=dict)

    class Meta:
        table_name = "runs"
    
    def log_stream(self) -> Generator[dict]:
        return (l.log_data for l in self.logs)

    def write_log(self, **kwargs) -> "Log":
        return Log.create(run=self, experiment=self.experiment, **kwargs)


class Log(BaseModel):
    run = ForeignKeyField(Run, backref="logs", null=False, on_delete="CASCADE")
    experiment = ForeignKeyField(
        Experiment, backref="logs", null=False, on_delete="CASCADE"
    )
    log_data = BinaryJSONField(null=False, default=dict)
    binary_data = PickleField(null=True)


    class Meta:
        table_name = "logs"


ALL_TABLES = BaseModel.__subclasses__()
