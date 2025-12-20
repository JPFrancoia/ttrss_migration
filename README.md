# TTRSS to Miniflux Migration Tool

A Python script to migrate articles and feeds from Tiny Tiny RSS (TTRSS) to Miniflux.

## What It Does

This tool migrates your RSS feed reading history from TTRSS to Miniflux, including:

- **Feeds**: All your subscribed feeds with their metadata
- **Articles**: All articles with their read/unread status
- **Starred articles**: TTRSS marked articles become starred in Miniflux
- **Tags and labels**: Combined into Miniflux tags
- **Published status**: TTRSS published articles are marked with vote=-1 in Miniflux

The migration runs in chunks with a progress bar, making it suitable for large databases.

## Requirements

- Python 3.13+
- Access to both TTRSS and Miniflux PostgreSQL databases
- Both databases should be accessible from where you run the script

## Installation

1. Clone this repository
2. Install dependencies using uv (recommended) or pip:

```bash
# Using uv
uv sync

# Using pip
pip install -e .
```

## Configuration

Set the following environment variables:

- `TTRSS_DATABASE_URL`: PostgreSQL connection string for your TTRSS database
- `MINIFLUX_DATABASE_URL`: PostgreSQL connection string for your Miniflux database
- `LOGGING_CONFIG`: (Optional) Path to logging configuration file (defaults to `dev_logging.conf`)

See `envrc_example` for the format.

## Usage

```bash
# Copy and edit environment file
cp envrc_example .envrc
# Edit .envrc with your database credentials
source .envrc

# Run the migration
python -m migration.main
```

Or set environment variables manually:

```bash
export TTRSS_DATABASE_URL="postgresql://user:password@localhost/ttrss"
export MINIFLUX_DATABASE_URL="postgresql://user:password@localhost/miniflux"
python -m migration.main
```

## Notes

- The script migrates articles to the default Miniflux user (ID: 1) and category (ID: 1)
- Articles from deleted feeds in TTRSS are skipped
- The migration is idempotent for feeds (based on feed_url) but may create duplicate articles if run multiple times
- Consider backing up your Miniflux database before running the migration

## Database Connection String Format

PostgreSQL connection strings follow this format:

```
postgresql://[user[:password]@][host][:port][/dbname]
```

Example:
```
postgresql://miniflux:secret@localhost:5432/miniflux
```


