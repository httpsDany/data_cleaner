# data_cleaner
A script to clean data in csv and xlsx format
<img width="957" height="333" alt="data_cleaner" src="https://github.com/user-attachments/assets/7091ce27-8b12-4436-8424-c72e7a69168d" />


TO INSTALL CODE:

  pip gitclone (link to repo)

TO-INSTALL REQUIREMENT:

  pip install -r requirements.txt

TO RUN THE CODE:

  python3 data_cleaner.py /path/to/file.(csv,xlsx)

Works with both windows and linux
Python base CLI tool

The tool can clean the 
-categorical column typo 
<img width="963" height="504" alt="data_cleaner03" src="https://github.com/user-attachments/assets/df8ccb7f-695d-4a7a-9d7e-0d7dca884bbf" />
-auto identify formats of column
<img width="959" height="309" alt="data_cleaner02" src="https://github.com/user-attachments/assets/c077ffba-7992-4aa2-a373-d04be6cbee5a" />

-detects missing column header
-remove null column
-handle duplicae rows
-handle unique columns
<img width="534" height="720" alt="data_cleaner01" src="https://github.com/user-attachments/assets/531ab7fd-107c-42f5-8f67-6e0100fbd886" />

-interactive with user as well

<img width="959" height="309" alt="data_cleaner02" src="https://github.com/user-attachments/assets/dd586a9f-da09-4cca-8121-0ed47836cc16" />

<img width="963" height="372" alt="data_cleaner04" src="https://github.com/user-attachments/assets/28ff5849-c0c9-4c30-b538-5599c4865c09" />



Drawback:

a)Using currency in CSV, make sure to put the currency column data inside double quote 

Example:  "20,000 thousand"

b) Cannot differentiate between currency type so in considers all currency the same

Example "INR 20,000" and "USD 2,000" is considered the same

*preffered using xlsx, but works with csv as well*
