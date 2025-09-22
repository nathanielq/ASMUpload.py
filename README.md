ASMUpload.py was created by me, Nate Quantock, to close the gap between Qmaltiv exports and Apple School Manager. Apple Classroom requires classes to be either manually created,
or automatically imported via Apple School Manager and Jamf Pro. 

How it works:
Six OneRoster formatted reports are exported to a specified location, like an ftp server.
classes, courses, rosters, locations, staff, and students are the six files that need to be uploaded to ASM.

Each file is written to a Pandas dataframe and the data is validated.
Depending on the file different rules are applied. Some are just as easy as confirming headers are correct, such is the case with the locations, courses,  and rosters files.

Student names that contain any sort of diacritic marks will export into unlegible text, so in these cases I used the script to rewrite their names accurately. This can be seen in lines 40 to 43.
We also have students that are enrolled at two schools, and this causes errors in ASM, so I delete whichever building they are the least. THis can be seen in lines 36 and 37 using df.drop.

Staff requires inserting a column between first_name and last_name and dropping the middle_initial column.

Classes requries a bit more. By default Qmlativ can export 2 instructors for a class. In certain instances a class might have 2+ paras that need access to Apple Classroom. We have a third csv
that we call 'instructor3-template.csv' where we map a staff id to class id. This part of the function will open that csv and will insert an instructor_id_3 column and then use df.loc to find the class
id index for the needed class and insert the staff id in to instructor_id_3.

Once files have been validated and written to a new folder, which I do just to keep things seperated and that way I have clean untouched files to reference, they are zipped into a single file
(required by ASM) and uploaded using Paramiko to the ASM sftp server.

Last Updated 9-22-2025
