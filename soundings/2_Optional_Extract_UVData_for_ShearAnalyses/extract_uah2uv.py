### NAME:  extract_uah2uv.py

### MODIFICATION HISTORY:  Written by Maiana Hanshaw for Python (03/22/2020);

### PURPOSE:  To extract U and V wind components from UAH, which is in its own format.

### RESTRICTIONS:
##   INCOMING UAH data needs to be in the format as shown below:

#VORTEX-SE 2017 UAH Radiosonde Data
#20170328, 0051 UTC, Brownsferry, AL, 201 m
#latitude (deg), longitude (deg),time (sec),height (m MSL),pressure(mb),temp (deg C),RH (%),dewpoint (deg C),Calculated wind speed (kts),Calculated wind direction (deg)
#34.73705, -87.12219, 0:52:2, 223.0, 984.3, 17.13, 86.1, 14.83, 8.2, 127 
#34.73712, -87.1223, 0:52:5, 242.0, 982.16, 17.43, 84.85, 14.9, 8.0, 116 
#34.73717, -87.12242, 0:52:8, 261.0, 979.9, 17.61, 83.4, 14.82, 14.2, 165 
#%END%

##   OUTGOING data will be a text file in the format:

#Project:               PECAN
#Platform ID/Location: 	MP1: OU
#Date/Time (UTC): 		CLAMPS/20150713
#Latitude/Longitude: 	43.50500/-91.85000
#Altitude (masl): 		418.0
#---------------------------------------------
#HEIGHT(masl)  WSPD(m/s)  WDIR  U(m/s)  V(m/s)
#   421.8        10.7     164    -3.0    10.3

### Although no flags exist in the UAH data, I have attempted to add some based on info from the log notes
#   and added these as -9999.

###############################################################################

import os  # operating system library
import pandas as pd  # pandas library for dictionary and data frames
import re  # regular expressions library
import math  # math library

###### UPDATE THIS ######
project = "VSE-2018"
directory_in = "C:/Users/Maiana/Downloads/Soundings/VSE-2018/Data/UAH"  # location of UAH sounding data files
directory_out = "C:/Users/Maiana/Downloads/Soundings/VSE-2018/Data/UAH/UV_Files"  # location to output "UV" text files
invalid_value = "-9999"
#########################

def get_files_from_directory(directory_in):

    selected_files = []
    for root, dirs, files in os.walk(directory_in):
        if root == directory_in:
            for file in files:
                if "upperair" in file:
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

########################

def parse_info_from_uah_file(file_in):

    print(file_in)  

    # Extract site info for site header from file name, and construct into "UV" format
    site_info = re.split(r'[_.\s]\s*', file_in)
 
    # Get site id/name
    inst_id = site_info[1]
    location = site_info[4]
    name = inst_id + ": " + location
        
    # Get date and time
    dt = site_info[3]
    date = dt[0:8]
    time = dt[8:12]
     
    # Get lat and lon
    file_lines = open_file_and_split_into_lines(file_in)
    latlon = file_lines[3].split()
    lt = float(latlon[0].strip(","))
    lat = '{:.5f}'.format(lt)
    ln = float(latlon[1].strip(","))
    lon = '{:.5f}'.format(ln)
            
    # Get initial height (as data sometimes has height starting at 0 m AGL and not at m aMSL)
    alt_line = file_lines[1].replace(" ","").split(",")
    alt = alt_line[4].rstrip()
    altitude = float(alt[:-1])

    ########################

    # Different header formats exist, so extract data depending on which you have    
    if "height (m MSL)"  in file_lines[2] and "Calculated" in file_lines[2]:
        col_headers = ["height (m MSL)", "Calculated wind speed (kts)", "Calculated wind direction (deg)"]
    elif "height (m MSL)"  in file_lines[2] and "Calculated" not in file_lines[2]:
        col_headers = ["height (m MSL)", "wind speed (kts)", "wind direction (deg)"]
    elif "height (m AGL)" in file_lines[2]:
        col_headers = ["height (m AGL)", "wind speed (kts)", "wind direction (deg)"]

    # Extract data header and data into a dictionary and then a data frame
    data_d = pd.read_csv(os.path.join(directory_in, file_in), sep=",", engine="python", header=2, skipfooter=1, usecols=col_headers).to_dict(orient="list")
    data_df = pd.DataFrame.from_dict(data_d, orient='columns').astype(float).sort_index()  # convert dictionary to a data frame with float numbers

    # Standardize column headers   
    if "height (m MSL)" in file_lines[2]:
        data_df.columns = ["Height (masl)", "WSPD (kts)", "WDIR (deg)"]      
    elif "height (m AGL)" in file_lines[2]:
        data_df["height (m AGL)"] += altitude  # add initial altitude to height values
        data_df.columns = ["Height (masl)", "WSPD (kts)", "WDIR (deg)"]

    # Convert variables to list
    h_temp = ["%.1f"%item for item in data_df["Height (masl)"].values.tolist()]
    ws_temp = data_df["WSPD (kts)"].values.tolist()
    wd_temp = data_df["WDIR (deg)"].values.tolist()
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
            
        # Add "-9999" if data is missing (-9999.0)
        if h_temp[ind] == invalid_value:
            h.append("{:>8}".format(str(invalid_value)))
        else:
            h.append("{:>8}".format(str(h_temp[ind])))
            
        if ws_temp[ind] == invalid_value:
            ws.append("{0:>11}".format(invalid_value))
        else:
            ws_temp[ind] = ws_temp[ind] / 1.94384  # knots to m/s
            ws_value = '{:.1f}'.format(ws_temp[ind])
            ws.append("{0:>11}".format(str(ws_value)))
            
        if wd_temp[ind] == invalid_value:
            wd.append("{:>8}".format(invalid_value))
        else:
            wd_value = '{:.1f}'.format(wd_temp[ind])
            wd.append("{:>8}".format(str(wd_value)))
     
    # Sometimes the last wind value is super funky, so check it and make ws and wd -9999 if necessary
    for ind in range(len(data_df)):
        if ind == (len(data_df)-1):
            wind = ws[ind]
            previous_wind = ws[ind-1]
            if wind > previous_wind * 3:
                ws[ind] = "{0:>11s}".format(invalid_value)
                wd[ind] = "{0:>8s}".format(invalid_value)
                
    # Calculate u and v
    for ind in range(len(ws_temp)):        
        # If wind speed is 0, set u and v to 0 also
        if float(ws[ind]) == 0.0:
            u.append("{:>6}".format(str("0.00")))
            v.append("{:>7}".format(str("0.00")))        
        # Otherwise continue to add flags
        elif float(ws[ind]) != 0.0 and (invalid_value in ws[ind] or invalid_value in wd[ind]):
            u.append("{:>7}".format(invalid_value))
            v.append("{:>7}".format(invalid_value))
        else:
            u_value = -ws_temp[ind] * math.sin(math.radians(wd_temp[ind]))
            u_temp[ind] = '{:.2f}'.format(u_value)
            u.append("{:>7}".format(str(u_temp[ind])))

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
   
    # Add relevant information to a dictionary
    sounding_file_dict = {}
    
    sounding_file_dict["file_in"] = file_in
    sounding_file_dict["inst_id"] = inst_id
    sounding_file_dict["location"] = location
    sounding_file_dict["site_name"] = name
    sounding_file_dict["date"] = date
    sounding_file_dict["time"] = time
    sounding_file_dict["lat"] = lat
    sounding_file_dict["lon"] = lon
    sounding_file_dict["alt"] = altitude
    sounding_file_dict["h_init"] = h_init
    sounding_file_dict["flag"] = flag
    sounding_file_dict["data"] = uv_data
    
    return sounding_file_dict

#########################

def output_to_uv_format(sounding_file_dict):

    # Construct site header
    site_header = ("Project: " + "\t\t\t\t{}" + "\n" + "Platform ID/Location: " + "\t{}" + "\n" + "Date/Time (UTC): " + "\t\t{}/{}" + "\n" + "Latitude/Longitude: " + "\t{}/{}" + "\n" 
                   + "Altitude (masl): " + "\t\t{}").format(project, sounding_file_dict["site_name"], sounding_file_dict["date"], sounding_file_dict["time"], sounding_file_dict["lat"], sounding_file_dict["lon"], sounding_file_dict["alt"])

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
  
    file_out = "UV_{}_{}_{}_{}.txt".format(sounding_file_dict["inst_id"], sounding_file_dict["location"], sounding_file_dict["date"], sounding_file_dict["time"])  # create output file name
                   
    whole_file = site_header + "\n" + "---------------------------------------------" + "\n" + data_header + "\n" + sounding_file_dict["data"]

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
    sounding_file_dict = parse_info_from_uah_file(file)
    uv_dict = output_to_uv_format(sounding_file_dict)

    # Incrementally append problem file names to a text file
    problem = ""
    alt_diff = sounding_file_dict["h_init"] - sounding_file_dict["alt"]
    if alt_diff >= 5:
        alt_diff_string = '{:.1f}'.format(alt_diff)
        problem += "Problem (Alt. Diff >= 5) = " + alt_diff_string
        
    if sounding_file_dict["flag"] != "":
        problem += "Problem = " + sounding_file_dict["flag"]

    if problem != "":
        with open(os.path.join(directory_out, "Problem_Files_UAH.txt"), "a+") as f:            
            f.seek(0)  # move cursor to the start of file            
            data = f.read(100) # if file is not empty then append '\n'
            if len(data) > 0:
                f.write("\n")
            # Append text to the end of the file
            f.write(file + ": " + problem)
           
    # Write converted files to text files    
    write_to_uv_files(uv_dict)

#############################################################################