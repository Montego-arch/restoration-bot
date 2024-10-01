# restoration_bot/cli.py

import click
from restoration_bot.database_restorer import DatabaseRestorer

@click.group(context_settings={ "help_option_names": ['-h', '--help']})
def entry_point():
    pass

@entry_point.command('run')
@click.option('--config', required=True, type=click.Path(exists=True), help='Path to the configuration file.')
def run_restoration(config):
    """Run the database restoration process."""
    restorer = DatabaseRestorer(config)     
    # restorer.run()
    print("Made it this far")


