import os
import time
import shutil
import subprocess
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuration
backup_dir = "/var/www/backup"  # Directory where backups will be stored
folder_to_backup = "/var/www/html/phpmyadmin"
database_name = "dbname"
mysql_user = "dbuser"
mysql_password = "dbpass"
num_backups_to_keep = 5

# Email configuration
smtp_server = "example.com"
smtp_port = 587
smtp_user = "email@example.com"
smtp_password = "password"
recipient_email = "email@example.com"
sender_email = "email@example.com"
sender_name = "Sender"


# Function to send email notifications
def send_email(subject, message):
    msg = MIMEMultipart()
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient_email
    msg["Subject"] = subject

    msg.attach(MIMEText(message, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")


try:
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Generate filenames based on the current timestamp
    timestamp = time.strftime("%d_%m_%Y__%H_%M_%S")
    backup_name = f"backup_{timestamp}.tar.gz"

    # Temporary directory to hold backup files
    temp_dir = os.path.join(backup_dir, f"temp_backup_{timestamp}")
    os.makedirs(temp_dir)

    # Backup the folder
    shutil.copytree(folder_to_backup, os.path.join(temp_dir, "myfolder"))

    # Backup the MySQL database
    db_backup_path = os.path.join(temp_dir, f"backup_db_{timestamp}.sql")
    command = f"mysqldump -u {mysql_user} -p{mysql_password} {database_name} > {db_backup_path}"
    subprocess.run(command, shell=True, check=True)

    # Compress both backups into a single archive
    backup_archive_path = os.path.join(backup_dir, backup_name)
    shutil.make_archive(backup_archive_path.replace(".tar.gz", ""), "gztar", temp_dir)

    # Cleanup the temporary directory
    shutil.rmtree(temp_dir)

    # Cleanup old backups
    backups = sorted(
        [
            f
            for f in os.listdir(backup_dir)
            if os.path.isfile(os.path.join(backup_dir, f))
        ]
    )
    if len(backups) > num_backups_to_keep:
        for old_backup in backups[:-num_backups_to_keep]:
            os.remove(os.path.join(backup_dir, old_backup))

    # Send success email
    send_email("Backup Successful", f"Backup completed successfully on {timestamp}")

except Exception as e:
    # Send failure email
    send_email("Backup Failed", f"Backup failed with error: {e}")
