### NAME:  copy_hgtfiles.py

### MODIFICATION HISTORY:  Written by Maiana Hanshaw for Python (03/14/2020)

### PURPOSE:  To extract all the CSWR "HGT" files for a given project into one folder.

###############################################################################

import os  # operating system library
import shutil  # sh utilities library

###### UPDATE THIS ######
directory_in = "C:/Users/Maiana/Desktop/Downloads/Soundings/RELAMPAGO/soundings-20200314"  # location of sounding data
directory_out = "C:/Users/Maiana/Desktop/Downloads/Soundings/RELAMPAGO/HGT_Files"  # location to output "HGT" sounding data files
#########################

def copy_hgtfiles_to_directory(directory_in):
    if not os.path.exists(directory_out):
        os.makedirs(directory_out)
    for root, dirs, files in os.walk(directory_in):
        for file in files:
    #        if "IOP04" in root:
                if "Hgt" in file:
                    shutil.copy2(root + "/" + file, directory_out)
             
###############################################################################
    
files_to_copy = copy_hgtfiles_to_directory(directory_in)

###############################################################################