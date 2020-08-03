### NAME:  split_cls2eol_pecan.py

### MODIFICATION HISTORY:  Written by Maiana Hanshaw (03/17/2020);

### PURPOSE:  To split (parse) sounding data in EOL format that comes in combined
#             ".cls" files and need to be split into individual sounding text files,
#             ultimately to output into "SPC" file format, which SHARPpy can read and simulate.

### RESTRICTIONS:
##   INCOMING data needs to be in the NCAR EOL ".cls" file format as shown below:

#Data Type:                         GAUS SOUNDING DATA/Ascending
#Project ID:                        PECAN
#Release Site Type/Site ID:         IOP 15
#Release Location (lon,lat,alt):    098 57.05'W, 40 30.93'N, -98.951, 40.516, 668.9
#UTC Release Time (y,m,d,h,m,s):    2015, 06, 25, 00:01:01
#...
#/
#Nominal Release Time (y,m,d,h,m,s):2015, 06, 25, 00:01:01
# Time  Press  Temp  Dewpt  RH    Ucmp   Vcmp   spd   dir   Wcmp     Lon     Lat   Ele   Azi    Alt    Qp   Qt   Qrh  Qu   Qv   QdZ
#  sec    mb     C     C     %     m/s    m/s   m/s   deg   m/s      deg     deg   deg   deg     m    code code code code code code
#------ ------ ----- ----- ----- ------ ------ ----- ----- ----- -------- ------- ----- ----- ------- ---- ---- ---- ---- ---- ----
#  -1.0  936.3  29.7  22.3  64.0   -1.9   -4.7   5.1  22.1 999.0  -98.951  40.516 999.0 999.0   658.0  1.0  1.0  1.0  1.0  1.0  9.0
#   0.0  936.2  29.7  21.8  61.6   -0.9   -4.1   4.2  11.8   3.0  -98.951  40.516 999.0 999.0   658.7  1.0  1.0  1.0  1.0  1.0 99.0
#....
#3907.0   89.3 -62.8 -89.1   2.5   -0.8   -6.9   6.9   6.6   5.7  -98.155  40.428 999.0 999.0 17348.2  1.0  1.0  1.0  1.0  1.0 99.0
#3908.0   89.2 -62.8 -89.1   2.5   -0.8   -6.8   6.8   7.1   5.7  -98.155  40.428 999.0 999.0 17354.1  1.0  1.0  1.0  1.0  1.0 99.0
#Data Type:                         GAUS SOUNDING DATA/Ascending
#Project ID:                        PECAN
#Release Site Type/Site ID:         IOP 15
#....

##   OUTGOING data just needs to be data for individual soundings.

###############################################################################

import os  # operating system library
import re  # regular expressions library

###### UPDATE THIS ######
directory_in = "C:/Users/Maiana/Desktop/Downloads/Soundings/PECAN/CLS_Files"  # location of "CLS" sounding data files
directory_out = "C:/Users/Maiana/Desktop/Downloads/Soundings/PECAN/EOL_Files"  # location to output "EOL" sounding data files
extension = "cls"
#########################

def get_files_from_directory_by_extension(directory_in, extension):

    selected_files = []
    for root, dirs, files in os.walk(directory_in):
        if root == directory_in:
            for file in files:
                if "." + extension in file:
                    selected_files += [file]   
    return selected_files
 
########################

def open_file_and_split_into_lines(file_in):
    file_lines = []
    with open (os.path.join(directory_in, file_in), "r") as myfile:
        for file_line in myfile:          
            file_lines.append(file_line)
    return file_lines

#########################

def process_single_file(file_in):
    
    print(file_in)
    file_lines = open_file_and_split_into_lines(file_in)       
            
    new_soundings = []
    line_num = 0
    pattern = re.compile("Data Type")
    for line in file_lines:
        line_num += 1
        if pattern.search(line) != None:
            new_soundings.append(line_num)

    sounding_dict = {}  # create dictionary to append all file names and data to

    # Split merged data set into individual data chunks
    l = len(new_soundings)
    for i in range(l):
        ind_data = []
        if i < l-1:
            start = new_soundings[i] - 1
            end = new_soundings[i+1]
            ind_data = file_lines[start:end-1]
            ind_data_string = "".join(ind_data)
        # Continue until you reach the end of the original file
        if i == l-1:
            start = new_soundings[i] - 1
            end = len(file_lines)
            ind_data = file_lines[start:end]
            ind_data_string = "".join(ind_data)

        # Get date/time information for file name                       
        dt = ind_data[4].split()
        y = ""
        m = ""
        d = ""
        for i, v in enumerate(dt):
            if i == 4:
                y = v.strip(",")
            if i == 5:
                m = v.strip(",")
            if i == 6:
                d = v.strip(",")
            if i == 7:
                time = v.replace(":","")[0:4]
        date = y + m + d

        # Get Site ID and name information for file name 
        location_id = ""
        name = ""           
        if "MINDEN" in file_in:
            location_id = "FP4"
            name = "MINDEN"    
        if "BREWSTER" in file_in:
            location_id = "FP5"
            name = "BREWSTER"
        if "CSU" in file_in:
            location_id = ""
            name = "CSU"
        if "NSSL1" in file_in:
            location_id = "NSSL"
            name = "1"
        if "NSSL2" in file_in:
            location_id = "NSSL"
            name = "2"
        if "ARM" in file_in:
            location_id = "FP1"
            name = "ARM"
        if "GREEN" in file_in:
            location_id = "FP2"
            name = "GREEN"
        if "CLAMPS" in file_in:
            location_id = "MP1"
            name = "OU_CLAMPS"
        if "UAH" in file_in:
            location_id = "MP2"
            name = "UAH_MIPS"
        if "SPARC" in file_in:
            location_id = "MP3"
            name = "UW_SPARC"
        if "MISS" in file_in:
            location_id = "MP4"
            name = "NCAR_MISS"
        if "NWS" in file_in:
            split = ind_data[2].split()
            location_id = "NWS"
            for i, v in enumerate(split):
                if i == 4:
                    name = v.strip(",").upper()
        elif location_id == "" and name == "":
            split = ind_data[2].split()
            for i, v in enumerate(split):
                if i == 4:
                    location_id = v.strip(",")
                if i == 5:
                    name = v.strip(",").upper() 
                                    
        # Create output file name
        if location_id == "":
            file_out = "EOL_{}_{}_{}.txt".format(name, date, time)
        elif location_id != "":
            file_out = "EOL_{}_{}_{}_{}.txt".format(location_id, name, date, time)
        
        sounding_dict.update({file_out: ind_data_string}) 

    return sounding_dict
       
#########################
       
def create_directory_out(directory_out):  # Check if directory exists, and if not, make it
    if not os.path.exists(directory_out):
        os.makedirs(directory_out)

#########################
    
def write_to_eol_files(dictionary):  # Write dictionary items to files
    for name, data in dictionary.items():
        with open(os.path.join(directory_out, name), "w+") as f:
            f.write(data)
            
#############################################################################
    
files_to_process = get_files_from_directory_by_extension(directory_in, extension)

for file in files_to_process:
    sounding_dict = process_single_file(file)
    
    for key in sounding_dict.keys():
        print(key)
        
    create_directory_out(directory_out)
    write_to_eol_files(sounding_dict)

#############################################################################