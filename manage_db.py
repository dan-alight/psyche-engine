import click
from psyche.models import Base
from sqlalchemy import create_engine

SQLITE_DB_FILE_NAME = "db.sqlite"
SQLITE_DB_URL = f"sqlite:///{SQLITE_DB_FILE_NAME}"

@click.group()
def cli():
  pass

@cli.command()
def create_tables():
  """Create the database tables."""
  engine = create_engine(SQLITE_DB_URL)
  Base.metadata.create_all(engine)
  click.echo("Database tables created.")

if __name__ == "__main__":
  cli()
