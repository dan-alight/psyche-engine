import click
import json
from psyche.models import Base
from psyche.models.openai_api_models import OpenAiApiProvider, OpenAiApiKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@click.group()
@click.option(
    "--db",
    default="db.sqlite",
    help="The SQLite database filename to use.",
)
@click.pass_context
def cli(ctx, db):
  """Manage the Psyche database."""
  ctx.ensure_object(dict)
  SQLITE_DB_FILENAME = db
  SQLITE_DB_URL = f"sqlite:///{SQLITE_DB_FILENAME}"
  ctx.obj["db_filename"] = SQLITE_DB_FILENAME
  ctx.obj["db_url"] = SQLITE_DB_URL

@cli.command()
@click.pass_context
def create_tables(ctx):
  """Create the database tables."""
  engine = create_engine(ctx.obj["db_url"])
  Base.metadata.create_all(engine)
  click.echo(f"Database tables created for {ctx.obj['db_filename']}.")

@cli.command()
@click.option("--file", default="seed.json")
@click.pass_context
def seed_tables(ctx, file):
  """
  Docstring for seed_tables
  """
  engine = create_engine(ctx.obj["db_url"])
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
