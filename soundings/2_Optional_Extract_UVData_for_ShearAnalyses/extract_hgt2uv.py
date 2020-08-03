### NAME:  extract_hgt2uv.py

### MODIFICATION HISTORY:  Written by Maiana Hanshaw for Python (03/22/2020);

### PURPOSE:  To extract U and V wind components from CSWR "HGT" formatted files.

### RESTRICTIONS:
##   INCOMING data needs to be in the "HGT" file format as shown below:

#   STN      DATE   GMT   HTS        LAT         LON
#SCOUT1  20181110  1504   324  -31.72873   -63.84466
#NLVL =2227
#       P      HT      TC      TD     DIR     SPD  QP QH QT QD QW        LON       LAT
#   965.1   324.4   33.70   19.70  345.96    8.00   1  1  3  3  1  -63.84466 -31.72873
#   965.0   325.0   33.47   19.49  346.01    8.00   1  1  3  3  1  -63.84466 -31.72873

##   OUTGOING data will be a text file in the format:

#Project:               PECAN
#Platform ID/Location: 	MP1: OU
#Date/Time (UTC): 		CLAMPS/20150713
#Latitude/Longitude: 	43.50500/-91.85000
#Altitude (masl): 		418.0
#---------------------------------------------
#HEIGHT(masl)  WSPD(m/s)  WDIR  U(m/s)  V(m/s)
#   421.8        10.7     164    -3.0    10.3

## Additionally:   - have removed duplicate values of height
#                  - have removed decreasing height values

### QUALITY CONTROL FLAGS:  Invalid value should be "-9999"
#       QP = Pressure
#       QH = Height
#       QT = Temp
#       QD = Dew Point
#       QW = Wind

#       3 = questionable/maybe - including these values for now
#       4 = objectively BAD
#       5 = visually BAD
#       9 = MISSING

###############################################################################

import os  # operating system library
import pandas as pd  # pandas library for dictionary and data frames
import re  # regular expressions library
import math  # math library

###### UPDATE THIS ######
project = "RELAMPAGO"
directory_in = "C:/Users/Maiana/Downloads/Soundings/RELAMPAGO/HGT_Files"  # location of "HGT" sounding data files
directory_out = "C:/Users/Maiana/Downloads/Soundings/RELAMPAGO/UV_Files"  # location to output "UV" text files
invalid_value = "-9999"
#########################

def get_files_from_directory(directory_in):

    selected_files = []
    for root, dirs, files in os.walk(directory_in):
        if root == directory_in:
            for file in files:
                if "Hgt" in file:
                    selected_files += [file]
    return selected_files

#########################

def open_file_and_split_into_lines(file_in):
    file_lines = []
    with open (os.path.join(directory_in, file_in), "r") as myfile:
        for file_line in myfile:          
            file_lines.append(file_line)
    return file_lines

#########################

def height_increasing(height, index, h, altitude):    
    higher = True
    if invalid_value not in height:       
        if index == 0:
            previous_height = altitude
            if -2 <= (float(height) - previous_height) <= 0:
                higher = True
            if (float(height) - previous_height) < -2:
                higher = False        
        if index != 0:
            previous_height = h[index - 1]            
            if invalid_value in previous_height:
                higher = height_increasing(height, index -1, h, altitude)
            else:
                higher = height > previous_height                
    return higher

#########################
    
def parse_info_from_hgt_file(file_in):

    print(file_in)  

    # Extract site info for site header from file name, and construct into "UV" format
    vehicle_info = re.split(r'[_.\s]\s*', file_in)
 
    # Get site/vehicle id/name
    vehicle = vehicle_info[2]
        
    # Get date and time
    date = vehicle_info[1]
    time = vehicle_info[3]
     
    # Get lat and lon
    file_lines = open_file_and_split_into_lines(file_in)
    latlon = file_lines[1].split()
    lat = ""
    lon = ""
    for i, v in enumerate(latlon):
        if i == 4:
            lt = float(v.strip(","))
            lat = '{:.5f}'.format(lt)
        if i == 5:
            ln = float(v.strip(","))
            lon = '{:.5f}'.format(ln)
            
    # Get initial altitude
    alt_line = file_lines[1].split()
    altitude = float(alt_line[3])

    ########################

    # Extract data header and data into a dictionary and then a data frame
    data_d = pd.read_csv(os.path.join(directory_in, file_in), sep="\s{1,}", engine="python", header=3, usecols=["HT", "SPD", "DIR", "QH", "QW"]).to_dict(orient="list")
    data_df = pd.DataFrame.from_dict(data_d, orient='columns').astype(float).sort_index()  # convert dictionary to a data frame with float numbers

    # Convert variables to list
    h_temp = ["%.1f"%item for item in data_df["HT"].values.tolist()]
    ws_temp = data_df["SPD"].values.tolist()
    wd_temp = data_df["DIR"].values.tolist()
    u_temp = [float(invalid_value)] * len(ws_temp)
    v_temp = [float(invalid_value)] * len(ws_temp)
       
    # Create new variables, put in good data, and replace bad data values with invalid value: "-9999"
    h = []
    ws = []
    wd = []
    u = []
    v = []     
    for ind in range(len(data_df)):
        # If wind speed is 0, set wind direction to -9999
        if float(ws_temp[ind]) == 0.00:
            wd_temp[ind] = float(invalid_value)
            
        # Add "-9999" if QC flags are missing (9), visually bad (5), or objectively bad (4)
        if data_df["QH"][ind] == 9 or data_df["QH"][ind] == 5 or data_df["QH"][ind] == 4:
            h.append("{:>8}".format(invalid_value))
        else:
            h.append("{:>8}".format(str(h_temp[ind])))
            
        if data_df["QW"][ind] == 9 or data_df["QW"][ind] == 5 or data_df["QW"][ind] == 4:
            ws.append("{:>11}".format(invalid_value))
            wd.append("{:>8}".format(invalid_value))
        else:
            ws_value = '{:.1f}'.format(ws_temp[ind])
            ws.append("{:>11}".format(str(ws_value)))
            wd_value = '{:.1f}'.format(wd_temp[ind])
            wd.append("{:>8}".format(str(wd_value)))

    # Calculate u and v
    for ind in range(len(ws_temp)):
        # If wind speed is 0, set u and v to 0 also
        if float(ws[ind]) == 0.0 and (data_df["QW"][ind] != 9 or data_df["QW"][ind] != 5 or data_df["QW"][ind] != 4):
            u.append("{:>6}".format(str("0.00")))
            v.append("{:>7}".format(str("0.00")))        
        # Otherwise continue to add flags
        elif float(ws[ind]) != 0.0 and (data_df["QW"][ind] == 9 or data_df["QW"][ind] == 5 or data_df["QW"][ind] == 4):
            u.append("{:>6}".format(invalid_value))
            v.append("{:>7}".format(invalid_value))
        else:
            u_value = -ws_temp[ind] * math.sin(math.radians(wd_temp[ind]))
            u_temp[ind] = '{:.2f}'.format(u_value)
            u.append("{:>6}".format(str(u_temp[ind])))

            v_value = -ws_temp[ind] * math.cos(math.radians(wd_temp[ind]))
            v_temp[ind] = '{:.2f}'.format(v_value)
            v.append("{:>7}".format(str(v_temp[ind])))

    #########################
    
    # Check if height values are increasing, and if not, make values -9999
    for index in range(len(data_df)):
        higher = height_increasing(h[index], index, h, altitude)
    
        if not higher:
            h[index] = "{0:>8s}".format(invalid_value)
            ws[index] = "{0:>11s}".format(invalid_value)
            wd[index] = "{0:>8s}".format(invalid_value)
            u[index] = "{0:>6s}".format(invalid_value)
            v[index] = "{0:>7s}".format(invalid_value)
            
    ######################## 
    
    # Put the data together
    uv_data_list = []  # create empty list to fill with correctly spaced data
   
    for ind in range(len(data_df)):
        if "-9999" in h[ind]:
            continue
        if h[ind] == h[ind-1]:
            continue
        height = h[ind]
        wspd = ws[ind]
        wdir = wd[ind]
        u_wind = u[ind]
        v_wind = v[ind]
            
        uv_string = "{} {} {} {} {}".format(height, wspd, wdir, u_wind, v_wind)  # create the new string for each row
        uv_data_list.append(uv_string)  # add each row into the new list

    uv_data = "\n".join(uv_data_list)  # join all the elements together again into a string

    #########################

    # Get info that could be problematic
    flag = ""
    if uv_data_list != []:
        h_line = uv_data_list[0].split()
        h_init = float(h_line[0])
    else:
        h_init = altitude
        flag = "FILE COMPLETELY EMPTY"
        
    h_flag_0 = data_df["QH"][0]
    h_flag_100 = data_df["QH"][100]
   
    # Add relevant information to a dictionary
    sounding_file_dict = {}
    
    sounding_file_dict["file_in"] = file_in
    sounding_file_dict["vehicle_name"] = vehicle
    sounding_file_dict["date"] = date
    sounding_file_dict["time"] = time
    sounding_file_dict["lat"] = lat
    sounding_file_dict["lon"] = lon
    sounding_file_dict["alt"] = altitude
    sounding_file_dict["h_init"] = h_init
    sounding_file_dict["flag"] = flag
    sounding_file_dict["h_flag_0"] = h_flag_0
    sounding_file_dict["h_flag_100"] = h_flag_100
    sounding_file_dict["data"] = uv_data
    
    return sounding_file_dict

#########################

def output_to_uv_format(sounding_file_dict):

    # Construct site header
    vehicle_header = ("Project: " + "\t\t\t\t{}" + "\n" + "Platform ID/Location: " + "\t{}" + "\n" + "Date/Time (UTC): " + "\t\t{}/{}" + "\n" + "Latitude/Longitude: " + "\t{}/{}" + "\n" 
                   + "Altitude (masl): " + "\t\t{}").format(project, sounding_file_dict["vehicle_name"], sounding_file_dict["date"], sounding_file_dict["time"], sounding_file_dict["lat"], sounding_file_dict["lon"], sounding_file_dict["alt"])

    # Construct data header
    height = "HEIGHT(masl)"
    wspd = "WSPD(m/s)"
    wdir = "WDIR"
    u_header = "U(m/s)"
    v_header = "V(m/s)"
    
    data_header = "{}  {}  {}  {}  {}".format(height, wspd, wdir, u_header, v_header)
    
    ########################

    # Add file_name and data to a dictionary which will then be printed out to text files
    uv_dict = {}
  
    file_in = sounding_file_dict["file_in"]
    file_out = file_in.replace("Hgt", "UV") + ".txt" # create output file name
                   
    whole_file = vehicle_header + "\n" + "---------------------------------------------" + "\n" + data_header + "\n" + sounding_file_dict["data"]

    uv_dict.update({file_out: whole_file}) # append file name (key) and data (value) to dictionary
       
    return uv_dict

#########################
       
def create_directory_out(directory_out):  # Check if directory exists, and if not, make it
    if not os.path.exists(directory_out):
        os.makedirs(directory_out)

#########################
    
def write_to_uv_files(dictionary):  # Write dictionary items to files
    for name, data in dictionary.items():
        with open(os.path.join(directory_out, name), "w+") as f:
            f.write(data)
                        
#############################################################################
    
files_to_process = get_files_from_directory(directory_in)
create_directory_out(directory_out)

for file in files_to_process:
    sounding_file_dict = parse_info_from_hgt_file(file)
    uv_dict = output_to_uv_format(sounding_file_dict)

    # Incrementally append problem file names to a text file
    problem = ""
    alt_diff = sounding_file_dict["h_init"] - sounding_file_dict["alt"]
    if alt_diff >= 5:
        alt_diff_string = '{:.1f}'.format(alt_diff)
        problem += "Problem (Alt. Diff >= 5) = " + alt_diff_string
        
    h_flag_string = ""    
    if sounding_file_dict["h_flag_0"] and sounding_file_dict["h_flag_100"] == 4:
        h_flag_string = "4 THROUGHOUT"
    elif sounding_file_dict["h_flag_0"] == 4 and sounding_file_dict["h_flag_100"] != 4:
        h_flag_string = "4 INITIALLY"            
    if h_flag_string != "":
        problem += "Problem (QH Flag) = " + h_flag_string
        
    if sounding_file_dict["flag"] != "":
        problem += "Problem = " + sounding_file_dict["flag"]

    if problem != "":
        with open(os.path.join(directory_out, "Problem_Files.txt"), "a+") as f:            
            f.seek(0)  # move cursor to the start of file            
            data = f.read(100) # if file is not empty then append '\n'
            if len(data) > 0:
                f.write("\n")
            # Append text to the end of the file
            f.write(file + ": " + problem)
           
    # Write converted files to text files    
    write_to_uv_files(uv_dict)

#############################################################################