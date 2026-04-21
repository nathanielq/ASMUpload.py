# # Config # #
# Imports
import keyring
# Misc
dual = {'student_ids of the dual enrolled students'}
# File Paths
# upload and source
upload_zip = "path_to_zip_file"
upload_folder = "path_to_folder_for_upload"
source_folder = "path_to_exported_files"
# ASM Files
students_file = 'path_to_students_file'
staff_file = 'path_to_staff_file'
rosters_file = 'path_to_rosters_file'
locations_file = 'path_to_locations_file'
courses_file = 'path_to_courses_file'
classes_file = 'path_to_classes_file'
# Logging
log_path = 'path_to_log'

# SFTP Variables
server = "upload.appleschoolcontent.com"
port = 22
username = "sftp_username"
password = keyring.get_password("ASMUpload",username)
r_path = "sftp_folder_path"

# Headers 
# insert your own necessary headers here
students = ['person_id', 'person_number', 'first_name', 'middle_name', 
            'last_name', 'grade_level', 'email_address', 'sis_username', 
            'password_policy', 'location_id', 'location_id_2']

staff =  ['person_id', 'person_number', 'first_name', 'middle_name', 
          'last_name', 'email_address', 'sis_username', 'location_id', 
          'location_id_2']

rosters = ['roster_id', 'class_id', 'student_id']

locations = ['location_id', 'location_name']

courses = ['course_id', 'course_number', 'course_name', 'location_id']

classes = ['class_id', 'class_number', 'course_id', 'instructor_id', 
           'instructor_id_2','instructor_id_3','instructor_id_4',
            'location_id', 'All Staff Names']
# File mapping

file_keys = {'rosters.csv': [rosters, rosters_file], 
             'locations.csv': [locations, locations_file],
            'courses.csv': [courses, courses_file]}




