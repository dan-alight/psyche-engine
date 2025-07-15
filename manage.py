# manage.py
import click
import json
import sys
import os  # Import the os module

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from psyche.config import SQLITE_DB_FILE_PATH
# Import your models so they are registered with the Base
from psyche.models import Base, AiProvider, ApiKey

_SYNC_SQLITE_DB_URL = f"sqlite:///{SQLITE_DB_FILE_PATH}"

@click.group()
def cli():
  """Database management commands."""
  pass

@cli.command()
def create_tables():
  """Creates all tables exported by models package."""
  engine = create_engine(_SYNC_SQLITE_DB_URL)
  click.echo("Creating all tables...")
  Base.metadata.create_all(engine)
  click.echo("✅ Tables created successfully.")

@cli.command()
def reset_db():
  """Drops all tables and recreates them. DELETES ALL DATA."""
  engine = create_engine(_SYNC_SQLITE_DB_URL)

  click.echo(f"Resetting database '{SQLITE_DB_FILE_PATH}'.")
  click.echo(f"Dropping all tables...")
  Base.metadata.drop_all(engine)
  click.echo("Tables dropped.")

  click.echo(f"Creating all tables...")
  Base.metadata.create_all(engine)
  click.echo("Tables created.")

  click.echo(f"Setting up triggers...")
  TRIGGER_INSERT = """
  CREATE TRIGGER update_conversation_last_updated_after_insert
  AFTER INSERT ON conversation_message
  FOR EACH ROW
  BEGIN
      UPDATE conversation
      SET last_updated = NEW.created_at
      WHERE id = NEW.conversation_id;
  END;
  """
  TRIGGER_DELETE = """
  CREATE TRIGGER update_conversation_last_updated_after_delete
  AFTER DELETE ON conversation_message
  FOR EACH ROW
  BEGIN
      UPDATE conversation
      SET last_updated = (
          SELECT MAX(created_at)
          FROM conversation_message
          WHERE conversation_id = OLD.conversation_id
      )
      WHERE id = OLD.conversation_id;
  END;
  """
  TRIGGER_UPDATE = """
  CREATE TRIGGER update_conversation_last_updated_after_update
  AFTER UPDATE ON conversation_message
  FOR EACH ROW
  BEGIN
      -- Always recalculate for the new conversation the message belongs to.
      UPDATE conversation
      SET last_updated = (
          SELECT MAX(created_at)
          FROM conversation_message
          WHERE conversation_id = NEW.conversation_id
      )
      WHERE id = NEW.conversation_id;

      -- Recalculate for the old conversation, but ONLY if its ID is
      -- different from the new conversation's ID.
      UPDATE conversation
      SET last_updated = (
          SELECT MAX(created_at)
          FROM conversation_message
          WHERE conversation_id = OLD.conversation_id
      )
      WHERE id = OLD.conversation_id AND NEW.conversation_id != OLD.conversation_id;
  END;
  """
  with engine.begin() as conn:
    conn.execute(text(TRIGGER_DELETE))
    conn.execute(text(TRIGGER_INSERT))
    conn.execute(text(TRIGGER_UPDATE))
  click.echo("Triggers created.")

  click.echo("✅ Database has been reset successfully.")

@cli.command()
@click.option(
    '--file', default='seed_data.json', help='Path to the seed data JSON file.')
def seed_db(file):
  """Seeds the database with data from a JSON file."""
  engine = create_engine(_SYNC_SQLITE_DB_URL)
  Session = sessionmaker(engine)

  click.echo(f"Seeding '{SQLITE_DB_FILE_PATH}' from {file}.")

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

def _copy_table(source_db_path: str, dest_db_path: str, table_name: str):
  """
    Copies a table from a source SQLite database to a destination SQLite database.

    This function is self-contained and creates its own engine. It will:
    1. Connect to the destination database (creating it if it doesn't exist).
    2. Check if the table exists in the destination. If it exists and contains
       data, the operation is aborted.
    3. If the table does not exist in the destination, its schema is recreated.
       If it exists but is empty, the schema creation is skipped.
    4. Copy all data from the source table to the destination table.

    Args:
        source_db_path: Path to the source .sqlite file.
        dest_db_path: Path to the destination .sqlite file.
        table_name: The name of the table to copy.

    Returns:
        The number of rows copied.

    Raises:
        FileNotFoundError: If the source database file does not exist.
        ValueError: If the table exists in the destination and is not empty,
                    or if the table is not found in the source.
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

      # 1. CHECK TABLE IN DESTINATION
      check_sql = text(
          f"SELECT name FROM {dest_alias}.sqlite_master WHERE type='table' AND name=:table_name"
      )
      table_exists = conn.execute(check_sql, {
          "table_name": table_name
      }).scalar_one_or_none() is not None

      if table_exists:
        # Table exists. Check if it's empty.
        count_sql = text(f"SELECT COUNT(*) FROM {dest_alias}.{table_name}")
        row_count = conn.execute(count_sql).scalar_one()
        if row_count > 0:
          raise ValueError(
              f"Table '{table_name}' already exists in destination "
              f"'{dest_db_path}' and is not empty.")
        # If we're here, table exists and is empty. We can proceed to copy.
      else:
        # Table does not exist. We need to create it.
        # Get schema from the attached source database
        schema_sql = text(
            f"SELECT sql FROM {source_alias}.sqlite_master WHERE type='table' AND name=:table_name"
        )
        schema_result = conn.execute(schema_sql, {
            "table_name": table_name
        }).scalar_one_or_none()
        if not schema_result:
          raise ValueError(
              f"Table '{table_name}' not found in source '{source_db_path}'.")

        # Create table in the destination ('main')
        conn.execute(text(schema_result))

      # 2. COPY DATA (This part is now common to both paths)
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
      f"Starting backup of '{table}' from '{SQLITE_DB_FILE_PATH}' to '{backup_file}'."
  )

  try:
    rows_copied = _copy_table(
        source_db_path=SQLITE_DB_FILE_PATH,
        dest_db_path=backup_file,
        table_name=table)
    click.echo(f"✅ {rows_copied} rows backed up.")
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
      f"Starting restore of '{table}' from '{backup_file}' to '{SQLITE_DB_FILE_PATH}'."
  )

  try:
    rows_copied = _copy_table(
        source_db_path=backup_file,
        dest_db_path=SQLITE_DB_FILE_PATH,
        table_name=table)
    click.echo(f"✅ {rows_copied} rows restored.")
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

@cli.command()
@click.option(
    '--table', default='journal_entry', help='Name of the table to restore.')
def restore_backup(table):
  # this should
  pass

if __name__ == "__main__":
  cli()
