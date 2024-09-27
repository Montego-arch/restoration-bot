# restoration_bot/cli.py

import click
from restoration_bot.database_restorer import DatabaseRestorer

@click.command()
@click.option('--config', required=True, type=click.Path(exists=True), help='Path to the configuration file.')
def run_restoration(config):
    """Run the database restoration process."""
    restorer = DatabaseRestorer(config)
    restorer.run()

if __name__ == '__main__':
    run_restoration()

