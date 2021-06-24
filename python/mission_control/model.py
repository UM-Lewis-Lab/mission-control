from uuid import uuid4

from peewee import ForeignKeyField, Model, CharField, SQL, UUIDField, BlobField
from playhouse.postgres_ext import BinaryJSONField, DateTimeField, PostgresqlExtDatabase

__all__ = ["postgres_db", "Project", "Experiment", "Run", "Log", "ALL_TABLES"]

postgres_db = PostgresqlExtDatabase(None)


class BaseModel(Model):
    uid = UUIDField(primary_key=True, default=uuid4, index=True, null=False)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        database = postgres_db


class Project(BaseModel):
    name = CharField(null=False, unique=True)
    metadata = BinaryJSONField(null=False, default=dict)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "projects"


class Experiment(BaseModel):
    name = CharField(null=False, unique=True)
    project = ForeignKeyField(
        Project, backref="experiments", null=False, on_delete="CASCADE"
    )
    metadata = BinaryJSONField(null=False, default=dict)

    class Meta:
        table_name = "experiments"


class Run(BaseModel):
    name = CharField(null=False, unique=True)
    experiment = ForeignKeyField(
        Experiment, backref="runs", null=False, on_delete="CASCADE"
    )
    metadata = BinaryJSONField(null=False, default=dict)

    class Meta:
        table_name = "runs"


class Log(BaseModel):
    run = ForeignKeyField(Run, backref="logs", null=False, on_delete="CASCADE")
    experiment = ForeignKeyField(
        Experiment, backref="logs", null=False, on_delete="CASCADE"
    )
    log_data = BinaryJSONField(null=False, default=dict)
    binary_data = BlobField(null=True)

    class Meta:
        table_name = "logs"


ALL_TABLES = BaseModel.__subclasses__()
