import logging
import os

def setup_logging():
    log_dir = "Logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 1. Main App Logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "app_activity.txt")),
            logging.StreamHandler()
        ]
    )

    # 2. Database Logger
    file_logger = logging.getLogger("file_ops")
    file_logger.setLevel(logging.INFO)
    file_logger.propagate = False 

    if not file_logger.handlers:
        fh = logging.FileHandler(os.path.join(log_dir, "file_operations.txt"))
        fh.setFormatter(logging.Formatter('%(asctime)s | %(message)s', '%Y-%m-%d %H:%M:%S'))
        file_logger.addHandler(fh)


# Logs data into the files logger (SPECIFICALLY FOR THE DISCORD BOT FILES)

def log_db_entry(data: dict) -> None:
    db_logger = logging.getLogger("file_ops")
    
    # Using a list and join() is often cleaner for multi-line reports
    report_lines = [
        f"\n{'__'*45}",
        "\n"

        f"DATABASE ENTRY LOG",
        f"{'-'*45}",
        f"FILE NAME:    {data.get('file_name')}",
        f"FILE TYPE:    {data.get('file_type')}",
        f"FILE PATH:    {data.get('file_path')}",
        f"USER:         {data.get('user')} (ID: {data.get('user_id')})",
        f"GROUP/DM:     {data.get('group_name')}",
        f"MESSAGE ID:   {data.get('message_id')}",
        f"CHANNEL ID:   {data.get('channel_id')}",

        "\n"
        f"{'- '*45}\n"
    ]
    
    report = "\n".join(report_lines)
    db_logger.info(report)