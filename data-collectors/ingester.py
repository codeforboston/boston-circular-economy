from enum import Enum

from data_transfer_objects import SQLQuery


class DBDialect(Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgres"


class Ingester:

    def __init__(self, connection, dialect: DBDialect = DBDialect.SQLITE):
        self.connection = connection
        self.dialect = dialect

    def write(self, records: list[SQLQuery]):
        pass
