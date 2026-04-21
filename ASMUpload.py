# Imports
# Config
import config
# Import Built in Modules
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Third Party Imports
import paramiko
import pandas as pd
import zipfile
import polars as pl

# Create the logger object #
logger = logging.getLogger('ASM Upload Log')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
handler = TimedRotatingFileHandler(config.log_path, when='D', interval=30, backupCount=12)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Delete the old Qmlativ exported files each run. (22 is appended in filename for old files since export runs at 9pm every night)
def delete_old_files():
    for file in Path(config.source_folder).glob( '*22*.csv'):
        try:
            os.remove(file)
            logger.info(f'Deleted {file.name}')
        # don't raise it really doesn't matter if these files are deleted. The upload is what matters.
        except Exception as e:
            logger.error(f'Could not delete files: {e}\n')

# process the students file and write to new location
def students_file(file):
    df = pd.read_csv(file) # left as pandas since its small granular changes
    # Some students are dual enrolled at elem and IMS. Look for the duplicate - check which one is the IMS record and delete that row (for now)
    drop_list = df.index[df['person_id'].isin(config.dual) & (df['location_id'] == 222) ]
    df = df.drop(drop_list)
    # Correct a student's name that is jacked up because of an accent above the e. Shout out computers.
    name_row = df.index[df['person_id']==71340]
    df.loc[name_row, 'first_name'] = 'Maelys'
    name_row = df.index[df['person_id'] == 66769]
    df.loc[name_row, 'last_name'] = 'Arevalo'

    df.to_csv(config.students_file, index=False)


# process staff file and write to new locaiton
def staff_file(file):
    df = pl.read_csv(file, null_values=[""])

    df = df.with_columns(pl.lit(None).alias('middle_name'))
    df = df.filter(pl.col('middle_initial').is_not_null())
    df = df.select('person_id', 'person_number', 'first_name','middle_name', 'last_name', 'email_address', 'sis_username', 'middle_initial','location_id 1')

    df.columns = config.staff
    df.write_csv(config.staff_file, separator=",")


# function for processing files that do not require any changes other than updating headers 
def other_files(file):
    df = pl.read_csv(file)
    df.columns = config.file_keys.get(file.name)[0]
    df.write_csv((config.file_keys.get(file.name)[1]), separator=",")


# function for processing the classes.csv file
def class_file(file):
    instructor_3_path = Path(config.source_folder) / 'instructor3-template.csv'

    # read in classes csv and cast columns as needed
    classes_df = (
        pl.read_csv(file, null_values=[""])
        .with_columns([
            pl.col('location_id').cast(pl.Utf8),
            pl.col('class_id').cast(pl.Int64),
            pl.col('instructor_id2').cast(pl.Int64),
        ])
    )
    # read in instructor3-template and read in instructor3/4 columns as dfs
    instructor_3_df = pl.read_csv(
        instructor_3_path,
        columns=[0, 1]
    ).with_columns(pl.col('class_id').cast(pl.Int64))

    instructor_4_df = pl.read_csv(
        instructor_3_path,
        columns=[0, 2]
    ).with_columns(pl.col('class_id').cast(pl.Int64))

    # Join instructor columns to classes df
    result_df = (
        classes_df
        .join(instructor_3_df, on='class_id', how='left')
        .join(instructor_4_df, on='class_id', how='left')
        .with_columns([
            pl.col('instructor_id_3').cast(pl.Utf8),
            pl.col('instructor_id_4').cast(pl.Utf8),
        ])
    )
    # Set the column order
    result_df = result_df.select(
        'class_id', 'class_number', 'course_id', 'instructor_id1', 'instructor_id2',
          'instructor_id_3', 'instructor_id_4', 'location_id' ,'All Staff Names'
        )

    # Rename to final headers and write to classes file
    result_df.columns = config.classes
    result_df.write_csv(config.classes_file)


            
# Iterate through files and trigger a different function for processing
def file_processor():
    for file in Path(config.source_folder).glob('*.csv'):
        if "students" in file.name:
            students_file(file)
        elif "staff" in file.name:
            staff_file(file)
        elif "rosters" in file.name or "locations" in file.name or "courses" in file.name:
            other_files(file)
        elif "classes" in file.name:
            class_file(file)

            
# send all the files to a zip folder (required for ASM uploads)
def zip_files():
    with zipfile.ZipFile(config.upload_zip, 'w') as zipf:
        for file in Path(config.upload_folder).glob('*.csv'):
            if "_" not in file.name:
                zipf.write(file, arcname=file.name)
                logger.info(f"Added '{file.name}' to '{config.upload_zip}'")
    logger.info(f"All ASM files have been added to '{config.upload_zip}'")
            
# clean up the folder after files have been uploaded (no raise here, file deletion is only a cleanup thing not dire)
def delete_files():
    for file in Path(config.upload_folder).glob('*'):
        try:
            os.remove(file)
            logger.info(f'deleted: {file.name}')
        except Exception as e:
            logger.error(f'Failed to delete file: {e}')
                       
# uploads the files to the ASM sftp server
def upload_file():
    transport = paramiko.Transport((config.server,22))
    sftp = None
    try:
        transport.connect(username=config.username, password=config.password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(config.upload_zip, config.r_path, confirm=False)
        logger.info(f"File {config.upload_zip} uploaded successfully to {config.r_path}")
    except Exception as e:
        if sftp is not None:
            sftp.close()
        transport.close()
        logger.critical(f"Error uploading zip file: {e}")
        raise
    finally:
        if sftp is not None:
            sftp.close()
        transport.close()

# function calls
if __name__ == '__main__':
    delete_old_files()
    file_processor()
    zip_files()
    upload_file()
    delete_files()