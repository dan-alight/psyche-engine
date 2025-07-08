# manage.py
import click
import json
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from psyche.config import SQLITE_DB_FILE_PATH
# Import your models so they are registered with the Base
from psyche.models import Base, AiProvider, ApiKey, AiModel

_SYNC_SQLITE_DB_URL = f"sqlite:///{SQLITE_DB_FILE_PATH}"
_engine = create_engine(_SYNC_SQLITE_DB_URL)
_Session = sessionmaker(_engine)

@click.group()
def cli():
  """Database management commands."""
  pass

@cli.command()
def reset_db():
  """Drops all tables and recreates them. DELETES ALL DATA.
  Afterwards, seeds the database with data from a JSON file."""
  if input("Are you sure you want to drop all data? [y/N]: ").lower() != 'y':
    click.echo("Aborted.")
    return
  click.echo("Dropping all tables...")
  Base.metadata.drop_all(_engine)
  click.echo("Tables dropped.")

  click.echo("Creating all tables...")
  Base.metadata.create_all(_engine)
  click.echo("Tables created.")

  click.echo("✅ Database has been reset successfully.")

@cli.command()
@click.option(
    '--file', default='seed_data.json', help='Path to the seed data JSON file.')
def seed_db(file):
  """Seeds the database with data from a JSON file."""
  click.echo(f"Seeding database from {file}...")

  try:
    with open(file, 'r') as f:
      data = json.load(f)
  except FileNotFoundError:
    click.echo(f"Error: Seed file '{file}' not found.", err=True)
    sys.exit(1)
  except json.JSONDecodeError:
    click.echo(f"Error: Could not decode JSON from '{file}'.", err=True)
    sys.exit(1)

  session = _Session()
  try:
    # A dictionary to hold the created provider objects, mapping name to object
    providers = {}

    # 1. Seed Providers first, as other models depend on them.
    click.echo("Seeding AI Providers...")
    for provider_data in data.get('aiprovider', []):
      provider = AiProvider(**provider_data)
      session.add(provider)
      providers[provider.name] = provider

    # Use flush to send the above INSERTs to the DB and get IDs,
    # but keep it all in one transaction.
    session.flush()

    # 2. Seed API Keys, linking them to the providers we just created.
    click.echo("Seeding API Keys...")
    for key_data in data.get('apikey', []):
      provider_name = key_data.pop('provider_name')
      provider_obj = providers.get(provider_name)
      if not provider_obj:
        click.echo(
            f"Warning: Provider '{provider_name}' not found for API key '{key_data.get('name')}'. Skipping.",
            err=True)
        continue

      # The magic of the ORM: assign the object to the relationship
      key = ApiKey(provider=provider_obj, **key_data)
      session.add(key)

    # 3. Commit the entire transaction
    session.commit()
    click.echo("✅ Database seeded successfully.")

  except Exception as e:
    click.echo(f"An error occurred: {e}", err=True)
    session.rollback()
    sys.exit(1)
  finally:
    session.close()

if __name__ == "__main__":
  cli()
