# manage.py
import click
import json
import sys
import os  # Import the os module

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from psyche.config import SQLITE_DB_FILE_PATH
# Import your models so they are registered with the Base
from psyche.models import Base, AiProvider, ApiKey, AiModel

_SYNC_SQLITE_DB_URL = f"sqlite:///{SQLITE_DB_FILE_PATH}"

@click.group()
def cli():
  """Database management commands."""
  pass

@cli.command()
def reset_db():
  """Drops all tables and recreates them. DELETES ALL DATA.
  Afterwards, seeds the database with data from a JSON file."""
  engine = create_engine(_SYNC_SQLITE_DB_URL)

  if input("Are you sure you want to drop all data? [y/N]: ").lower() != 'y':
    click.echo("Aborted.")
    return
  click.echo("Dropping all tables...")
  Base.metadata.drop_all(engine)
  click.echo("Tables dropped.")

  click.echo("Creating all tables...")
  Base.metadata.create_all(engine)
  click.echo("Tables created.")

  click.echo("✅ Database has been reset successfully.")

@cli.command()
@click.option(
    '--file', default='seed_data.json', help='Path to the seed data JSON file.')
def seed_db(file):
  """Seeds the database with data from a JSON file."""
  engine = create_engine(_SYNC_SQLITE_DB_URL)
  Session = sessionmaker(engine)

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

  session = Session()
  try:
    # A dictionary to hold the created provider objects, mapping name to object
    providers = {}

    # 1. Seed Providers first, as other models depend on them.
    click.echo("Seeding AI Providers...")
    for provider_data in data.get('ai_providers', []):
      provider = AiProvider(**provider_data)
      session.add(provider)
      providers[provider.name] = provider

    # Use flush to send the above INSERTs to the DB and get IDs,
    # but keep it all in one transaction.
    session.flush()

    # 2. Seed API Keys, linking them to the providers we just created.
    click.echo("Seeding API Keys...")
    for key_data in data.get('api_keys', []):
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

# --- NEW GENERIC HELPER FUNCTION ---
def _copy_table(source_db_path: str, dest_db_path: str, table_name: str):
  """
    Copies a table from a source SQLite database to a destination SQLite database.

    This function is self-contained and creates its own engine. It will:
    1. Connect to the destination database (creating it if it doesn't exist).
    2. Abort if the table already exists in the destination.
    3. Recreate the table schema in the destination.
    4. Copy all data from the source table to the destination table.

    Args:
        source_db_path: Path to the source .sqlite file.
        dest_db_path: Path to the destination .sqlite file.
        table_name: The name of the table to copy.

    Returns:
        The number of rows copied.

    Raises:
        FileNotFoundError: If the source database file does not exist.
        ValueError: If the table already exists in the destination or is not found in the source.
    """
  if not os.path.exists(source_db_path):
    raise FileNotFoundError(f"Source database '{source_db_path}' not found.")

  # Create an engine connected to the DESTINATION database.
  # This function is self-contained and does not use the global _engine.
  dest_engine = create_engine(f"sqlite:///{dest_db_path}")

  source_alias = "source_db"
  dest_alias = "main"  # 'main' is the default alias for the connected db

  try:
    with dest_engine.begin() as conn:
      # Attach the source database to the destination connection
      attach_sql = text(f"ATTACH DATABASE :source_path AS {source_alias}")
      conn.execute(attach_sql, {"source_path": source_db_path})

      # 1. SAFETY CHECK: Abort if table exists in destination ('main')
      check_sql = text(
          f"SELECT name FROM {dest_alias}.sqlite_master WHERE type='table' AND name=:table_name"
      )
      if conn.execute(check_sql,
                      {"table_name": table_name}).scalar_one_or_none():
        raise ValueError(
            f"Table '{table_name}' already exists in destination '{dest_db_path}'."
        )

      # 2. Get schema from the attached source database
      schema_sql = text(
          f"SELECT sql FROM {source_alias}.sqlite_master WHERE type='table' AND name=:table_name"
      )
      schema_result = conn.execute(schema_sql, {
          "table_name": table_name
      }).scalar_one_or_none()
      if not schema_result:
        raise ValueError(
            f"Table '{table_name}' not found in source '{source_db_path}'.")

      # 3. Create table in the destination ('main')
      conn.execute(text(schema_result))

      # 4. Copy data from source to destination
      copy_sql = text(
          f"INSERT INTO {dest_alias}.{table_name} SELECT * FROM {source_alias}.{table_name}"
      )
      result = conn.execute(copy_sql)

      # The 'with' block commits the transaction here.
      return result.rowcount

  finally:
    # Always try to detach the source database for clean-up.
    with dest_engine.connect() as conn:
      try:
        detach_sql = text(f"DETACH DATABASE {source_alias}")
        conn.execute(detach_sql)
      except Exception:
        # This may fail if the initial attach failed; we can ignore it
        # as the primary error has already been raised.
        pass

@cli.command()
@click.option(
    '--table', default='journal_entry', help='Name of the table to back up.')
@click.option(
    '--backup-file',
    default='backup.sqlite',
    help='Path to the backup database file.')
def backup_table(table, backup_file):
  """Backs up a table from the main database to a separate backup file."""
  click.echo(
      f"Starting backup of '{table}' from '{SQLITE_DB_FILE_PATH}' to '{backup_file}'..."
  )

  try:
    rows_copied = _copy_table(
        source_db_path=SQLITE_DB_FILE_PATH,
        dest_db_path=backup_file,
        table_name=table)
    click.echo(f"{rows_copied} rows backed up.")
    click.echo(f"✅ Backup of table '{table}' completed successfully.")
  except (ValueError, FileNotFoundError) as e:
    click.echo(f"Error: {e}", err=True)
    sys.exit(1)
  except Exception as e:
    click.echo(f"An unexpected error occurred: {e}", err=True)
    sys.exit(1)

@cli.command()
@click.option(
    '--table', default='journal_entry', help='Name of the table to restore.')
@click.option(
    '--backup-file',
    default='backup.sqlite',
    help='Path to the backup database file to restore from.')
def restore_table(table, backup_file):
  """Restores a table from a backup file into the main database."""
  click.echo(
      f"Starting restore of '{table}' from '{backup_file}' to '{SQLITE_DB_FILE_PATH}'..."
  )

  try:
    rows_copied = _copy_table(
        source_db_path=backup_file,
        dest_db_path=SQLITE_DB_FILE_PATH,
        table_name=table)
    click.echo(f"{rows_copied} rows restored.")
    click.echo(f"✅ Restore of table '{table}' completed successfully.")
  except ValueError as e:
    click.echo(f"Error: {e}", err=True)
    click.echo(
        "Aborting restore. Your main database has not been changed.", err=True)
    sys.exit(1)
  except FileNotFoundError as e:
    click.echo(f"Error: {e}", err=True)
    sys.exit(1)
  except Exception as e:
    click.echo(f"An unexpected error occurred: {e}", err=True)
    sys.exit(1)

if __name__ == "__main__":
  cli()
