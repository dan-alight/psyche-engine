import click
import json
from psyche.models import Base
from psyche.models.openai_api_models import OpenAiApiProvider, OpenAiApiKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

@cli.command()
@click.option("--file", default="seed.json")
def seed_tables(file):
  """
  Docstring for seed_tables
  """
  engine = create_engine(SQLITE_DB_URL)
  Session = sessionmaker(engine)
  click.echo(f"Seeding data from {file}.")
  with open(file, 'r') as open_file:
    data = json.load(open_file)
  with Session() as session:
    providers: dict[str, OpenAiApiProvider] = {}
    for provider_data in data.get("openai_api_providers", []):
      provider = OpenAiApiProvider(**provider_data)
      session.add(provider)
      providers[provider.name] = provider
    session.flush()  # get ids
    for key_data in data.get("openai_api_keys", []):
      provider_name = key_data.pop("provider_name")
      provider = providers.get(provider_name)
      if not provider:
        click.echo(
            f"Warning: no provider found with name {provider_name}", err=True)
        continue
      key = OpenAiApiKey(provider_id=provider.id, **key_data)
      session.add(key)
    session.commit()

if __name__ == "__main__":
  cli()
