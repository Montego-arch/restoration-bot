import os
import sys
import toml
import paramiko
from datetime import datetime
from typing import Dict, List
import logging






class DatabaseRestorer():

    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.logger = self.set_logging()
        self.ssh_client = None

    
    def load_config(self, config_path) -> Dict:
        try:
            return toml.load(config_path)
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def setup_logging(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler('restore_log.txt')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger
    
    def connect_ssh(self):
        ssh_config = self.config['ssh']
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
        """
        Automatically examines PRODUCTION SQL backups and downloads the latest one.
        """
        sftp = self.ssh_client.open_sftp()
        backups_dir = self.config['backup']['directory']

        try:
            backups = sorted(sftp.listdir(backups_dir))
            latest_backup = backups[-1]
            return (f"{backups_dir}/{latest_backup}")
        except Exception as e:
            self.logger.error(f"Failed to get latest backup: {e}")
            sys.exit(1)


