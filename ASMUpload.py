import paramiko
import os
import zipfile
import time
import pandas as pd
import sys
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)

Log_File = 'Path to log file'
sys.stdout = open(Log_File, 'a')
sys.stderr = sys.stdout
print(f'\nStarting ASMUpload.py at {datetime.now()}\n\n')

#Q Exports overwrite existing and append the time to them, runs at 10pm so 22 is in the filename of old ones
def Delete_Old_Files(folder):
    for filename in folder.glob('*.csv'):
        if '22' in filename.name: #Update to your time, or other identifier 22 was easiest for us
            os.remove(filename)
            print(f'Deleted {filename}')
            
#Data validation for all 6 oneroster files. Files are then written to a new folder for cleanliness
def Fix_Headers(folder_path):
    for filename in folder_path.glob('*.csv'):
        dual_students = {'list of dual enrolled students'}
        #confirms the headers for students file and deletes the old csv
        if "students" in filename.name:
            df = pd.read_csv(filename)
            students_header = ['person_id', 'person_number', 'first_name', 'middle_name', 'last_name', 'grade_level', 'email_address', 'sis_username', 'password_policy', 'location_id', 'location_id_2']
            df.columns = students_header
            #Some students are dual enrolled at elem and IMS. Look for the duplicate - check which one is the IMS record and delete that row (for now)
            #look by creating a list of index labels and dropping those. find all rows in the person_id column are in dual_students & have a location_id equal to the school they are at the least.
            drop_list = df.index[ df['person_id'].isin(dual_students) & (df['location_id'] == 'LOCATION_ID_HERE') ]
            df = df.drop(drop_list)
            #Correct a student's name that is jacked up because of an accent above the e. Shout out computers.
            try:
                name_row = df.index[df['person_id']=='id']
                df.loc[name_row, 'first_name'] = 'name'
                name_row = df.index[df['person_id'] == 'id']
                df.loc[name_row, 'last_name'] = 'name'
            except Exception as e:
                print(f'error: {e} could not process student ids')
            df.to_csv('Path to folder for finished CSVs', index=False) #User Dependent

        #confirms the headers for staff and creates the middle_name column and deletes the old csv
        elif "staff" in filename.name:
            df = pd.read_csv(filename)
            position = df.columns.get_loc('first_name') + 1
            df.insert(position, 'middle_name', pd.Series([None]*len(df))) #insert empty column after 'first_name' which replaces the middle initial one
            #Gets list of all non empty middle initial value and then sets those values to the location_id at the same index
            df.loc[df['middle_initial'].notna(), 'location_id 1'] = df['middle_initial']
            df.drop('middle_initial', axis=1, inplace=True) #delete middle initial column
            staff_header = ['person_id', 'person_number', 'first_name', 'middle_name', 'last_name', 'email_address', 'sis_username', 'location_id', 'location_id_2']
            df.columns = staff_header

            drop_list = df.index[df['location_id'].isna()]
            df = df.drop(drop_list)
            df['location_id'] = df['location_id'].astype(str)

            df.to_csv('Path to folder for finished CSVs', index=False) #User Dependent

        #confirms headers for rosters file and deletes the old csv
        elif "rosters" in filename.name:
            df = pd.read_csv(filename)
            rosters_header = ['roster_id', 'class_id', 'student_id']
            df.columns = rosters_header
            df.to_csv('Path to folder for finished CSVs', index=False) #User Dependent

        #confirms the headers for locations file and deletes the old csv
        elif "locations" in filename.name:
            df = pd.read_csv(filename)
            locations_header = ['location_id', 'location_name']
            df.columns = locations_header
            df.to_csv('Path to folder for finished CSVs', index=False) #User Dependent

        #confirms the headers for courses file and deletes the old csv
        elif "courses" in filename.name:
            df = pd.read_csv(filename)
            courses_header = ['course_id', 'course_number', 'course_name', 'location_id']
            df.columns = courses_header
            df.to_csv('Path to folder for finished CSVs', index=False) #User Dependent
        #confirms headers for classes file, performs a VLOOKUP with the para file and correctly inserts instructor_id_3 columns with the necessary values inserted. Deletes the old xlsx file.
        elif "classes" in filename.name:
            #load dataframes for classes.csv and instructor-3template.csv
            instructor_path = folder_path / 'instructor3-template.csv'
            instructor_df = pd.read_csv(instructor_path, usecols=[0,1])
            classes_path = folder_path / 'classes.csv'
            classes_df = pd.read_csv(classes_path)
            classes_df['location_id'] = classes_df['location_id'].astype(str) #prevent location_ids becoming decimals
            classes_df['instructor_id2'] = classes_df['instructor_id2'].astype('Int64') #prevent decimals, but in a way that does not try to cast empty cells

            #insert the instructor_id_3 column
            position = classes_df.columns.get_loc('instructor_id2') + 1
            classes_df.insert(position, 'instructor_id_3',  pd.Series([None]*len(classes_df)))

            #cast items as strings and create a dictionary from the instructor dataframe
            instructor_df['class_id'] = instructor_df['class_id'].astype('Int64')
            instructor_df['instructor_id_3'] = instructor_df['instructor_id_3'].astype('string')
            instructor_dict = dict(instructor_df.values)
            #Iterate through instructor_dict and match the class_id value in the classes.csv to find the row index then using that index write the instructor_id 
            # in the id_3 column that is at that row_index (Basically a simple Vlookup using Pandas dataframes which is so cool)
            for key, value in instructor_dict.items():
                class_row = classes_df.index[classes_df['class_id'] == key]
                classes_df.loc[class_row, 'instructor_id_3'] = value

            #Rewrite the headers with correct items
            classes_headers = ['class_id', 'class_number', 'course_id', 'instructor_id', 'instructor_id_2', 'instructor_id_3', 'location_id', 'All Staff Names']
            classes_df.columns = classes_headers
            classes_df.to_csv('Path to new folder for finished csvs', index=False)
            
#send all the files to a zip folder
def Zip_Files(folder_path, zip_file):
    with zipfile.ZipFile(zip_file, 'w') as zipf:
        for filename in folder_path.glob('*.csv'):
            if "_" not in filename.name:
                zipf.write(filename, arcname=filename.name)
                print(f"Added '{filename}' to '{zip_file}'")
    print(f"All ASM files have been added to '{zip_file}'")
            
#clean up the folder after files have been uploaded
def Delete_Files(folder_path):
    for filename in folder_path.glob('*'):
        if "_" not in filename.name:
            try:
                os.remove(filename)
            except OSError as e:
                print(f"Error deleting '{filename}': {e.strerror}")

        
#uploads the files to the ASM sftp server
def Upload_File(server, port, username, password, local_path, remote_path):
    transport = paramiko.Transport((server,port))
    transport.connect(username=username, password=password)

    sftp = paramiko.SFTPClient.from_transport(transport)

    try:
        sftp.put(local_path, remote_path, confirm=False)
        print(f"File {local_path} uploaded successfully to {remote_path}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sftp.close()
        transport.close()

#variables 
#ASM server info is pulled from Settings page in ASM
upload_server = "upload.appleschoolcontent.com"
port = 22
upload_username = "Username"
upload_password = "Password"
remote_path = "/dropbox/Archive.zip"

#User Dependent Variables
local_path = Path("Path To Final Zip File")
folder_path = Path("Path To Folder For Placing Manipualted CSVs") 
source_path = Path("Path where original files are grabbed from (QMlativ Exports)")

#function calls
if __name__ == '__main__':
    Delete_Old_Files(source_path)
    Fix_Headers(source_path)
    Zip_Files(folder_path, local_path)
    Upload_File(upload_server, port, upload_username, upload_password, local_path, remote_path)
    time.sleep(5)
    Delete_Files(folder_path)
    print(f'\n\nFinished running ASMUpload.py at {datetime.now()}\n')
    
