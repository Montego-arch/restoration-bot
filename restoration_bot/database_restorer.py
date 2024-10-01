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

    def download_backup(self, remote_path):
        sftp = self.ssh_client.open_sftp()
        local_path = os.path.basename(remote_path)

        try:
            sftp.get(remote_path, local_path)
            local_path = os.path.basename(remote_path)
            return local_path
        except Exception as e:
            self.logger.erro(f"Failed to download backup: {e}")
            sys.exit(1)

    def cleanup_old_backups(self):
        max_backups = self.config['backup']['max_keep']
        backups_dir= self.config['backup']['local_directory']

        backups = sorted(os.listdir(backups_dir))
        for backup in backups[:-max_backups]:
            os.remove(os.path.join(backups_dir, backup))
            self.logger.info(f"Removed old backup: {backup}")

    def restore_database(self, backup_path):
        db_config = self.config['database']
        mariadb_config = self.config['mariadb']

        self.stop_services()
        self.remove_old_db_files()
        self.restore_from_backup(mariadb_config['datadir'], backup_path)
        self.set_permissions(mariadb_config['datadir'])
        self.restart_mariadb()
        self.update_passwords(db_config['username'], db_config['password'])
        self.apply_patches(db_config['database_name'])


    def stop_services(self):
        services = self.config['services']['stop']
        for service in services:
            os.system(f"sudo systemctl stop {service}")
            self.logger.info("Stopped service: {service}")

    def remove_old_db_files(self):
        mariadb_datadir = self.config['mariadb']['datadir']
        os.system(f"sudo rm -f {mariadb_datadir}/*")
        self.logger.info("Removed old database files")

    def restore_from_backup(self, datadir, backup_path):
        command = f"sudo mariabackup --copy-back --datadir={datadir} --target-dir={backup_path}"
        os.system(command)
        self.logger.info("Restored database from backup")

    def set_permissions(self,datadir):
        os.system(f"sudo chown -R mysql:mysql {datadir}")
        self.logger.info("Set permissions for restored database")

    def restart_mariadb(self):
        os.system("sudo systemctl restart mariadb.service")
        self.logger.info("Restarted MariaDB service")


    def update_passwords(self, username, password):
        conn = mysql.connector.connect(
            host = self.config['database']['host'],
            user = username,
            password = password,
            database = self.config['database']['database_name']
        )              
        cursor = conn.cursor()
        cursor.execute("UPDATE mysql.user SET authentication_string=PASSWORD(%s) WHERE User=%s", (password, username))
        conn.commit()
        cursor.close()
        conn.close()
        self.logger.info(f"Updated password for user: {username}")

    
    def apply_patches(self, database_name):
        patches = self.config['patches']
        conn = mysql.connector.connect(
            host = self.config['database']['host'],
            user = self.config['database']['username'],
            password = self.config['database']['password'],
            database = database_name
        )
        cursor = conn.cursor()
        self.apply_email_patch(cursor, patches['email'])
        conn.commit()
        cursor.close()
        conn.close()
        self.logger.info("Applied patches")

    def apply_email_patch(self, cursor, email_config):
        customer_emails = email_config['customers']
        query = "UPDATE `tabCustomer` SET `email_id` = NULL WHERE `email_id` NOT IN (%s)"
        placeholders = ', '.join(['%s'] * len(customer_emails))
        cursor.execute(query % placeholders, tuple(customer_emails))

    def start_services(self):
        services = self.config['services']['start']
        for service in services:
            os.system(f"sudo systemctl start {service}")
            self.logger.info(f"Started service: {service}")

    def run(self):
        try:
            self.connect_ssh()
            latest_backup = self.get_latest_backup()
            backup_path = self.download_backup(latest_backup)
            self.cleanup_old_backups()
            self.restore_database(backup_path)
            self.start_services()
            self.logger.info("Database restoration completed successfully")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

