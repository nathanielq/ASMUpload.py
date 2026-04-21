#ASM Upload

##Description:
Need to upload files exported from our SIS to Apple School Manager to generate rosters in Apple Classroom. This bridges the gap.

##Tech Stack:
Python, Paramiko, Polars, Pandas, TimedRotatingFileHandler

## How it works:
Six files are exported from our SIS containing class, course, roster, student, staff, and location information. Each file is validated to have correct formatting and headers to match Apple School Manager. Classes files will be combined with a file called instructor3-template.csv to include any additional instructors in each class (our SIS only includes 2 instructors, but there might be upwards of 4 needed). Student file is cleaned up for any errors that occur with dual-enrolled students, or students containing accent marks that might result in wonky data. Once files are cleaned up they are sent to a zip file and uploaded to the sftp server for ASM. This will automatically generate rostering information for Apple Classroom.
