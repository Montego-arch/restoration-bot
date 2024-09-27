import os
import sys
import paramiko
import mysql.connector
from .config import load_config
from .logger import setup_logging
from .utils import validate_datatype

class DatabaseRestorer:
    def __init__(self, config_path):
        self.config = load_config(config_path)
        self.logger = setup_logging()
        self.ssh_client = None

    def connect_ssh(self):
        ssh_config = self.config['ssh']
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh_client.connect(
                hostname = ssh_config['hostname'],
                username = ssh_config['username'],
                password = ssh_config['password']

            )
        except Exception as e:
            self.logger.error(f"Failed to connect via SSH: {e}")
            sys.exit(1)

    def disconnect_ssh(self):
        if self.ssh_client:
            self.ssh_client.close()

    def get_latest_backup(self) -> str:
        sftp = self.ssh_client.open_sftp()
        backups_dir = self.config['backup']['directory']

        try:
            backups = sorted(sftp.listdir(backups_dir))
            latest_backup = backups[-1]
            return f"{backups_dir}/{latest_backup}"
        except Exception as e:
            self.logger.error(f"Failed to get latest backup: {e}")
            sys.exit(1)