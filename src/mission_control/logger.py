import csv
from typing import TextIO, Sequence
from pathlib import Path
from datetime import datetime as datetime


class CSVLogger:
    def __init__(self, path: Path, fields: Sequence[str]):
        self.path = path
        self.fields = fields

        self.timestamp_fieldname = "timestamp"
        if self.timestamp_fieldname in self.fields:
            raise ValueError(
                "Fieldname 'timestamp' is reserved, please use a different name."
            )
        self.fields.append(self.timestamp_fieldname)

        self.file: TextIO = self.path.open("w")
        self.writer = csv.DictWriter(self.file, self.fields)
        self.writer.writeheader()

    def write(self, **fields):
        fields[self.timestamp_fieldname] = datetime.now().isoformat()
        self.writer.writerow(fields)

    def __delete__(self):
        self.file.close()
