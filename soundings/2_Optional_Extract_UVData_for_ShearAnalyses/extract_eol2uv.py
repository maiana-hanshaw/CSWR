### NAME:  extract_eol2uv.py

### MODIFICATION HISTORY:  Written by Maiana Hanshaw for Python (03/22/2020);

### PURPOSE:  To extract U and V wind components from "EOL" formatted files as produced by other institutions

### RESTRICTIONS:
##   INCOMING data needs to be in the "EOL" file format as shown below:

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

##   OUTGOING data will be a text file in the format:

#Project: 				PECAN
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
#       Qp = Pressure
#       Qt = Temp
#       Qrh = Relative Humidity
#       Qu = Wind-u
#       Qv = Wind-v

#       2 = questionable/maybe - including these values for now
#       3 = BAD
#       9 = MISSING
#       99 = MISSING/UNCHECKED

###############################################################################

import os  # operating system library
import pandas as pd  # pandas library for dictionary and data frames
import re  # regular expressions library

###### UPDATE THIS ######
project = "RELAMPAGO"
directory_in = "C:/Users/Maiana/Downloads/Soundings/RELAMPAGO/CSU/EOL_Files"  # location of "EOL" sounding data files
directory_out = "C:/Users/Maiana/Downloads/Soundings/RELAMPAGO/CSU/UV_Files"  # location to output "UV" text files
invalid_value = "-9999"
#########################

def get_files_from_directory(directory_in):
    
    selected_files = []
    for root, dirs, files in os.walk(directory_in):
        if root == directory_in:
            for file in files:
                if "EOL" in file:
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

def parse_info_from_eol_file(file_in):
    
    print(file_in)
    
    # Extract site info for site header from file name, and construct into "UV" format
    site_info = re.split(r'[_.\s]\s*', file_in)
 
    # Get site id/name
    if len(site_info) == 5:
        name = site_info[1]
    if len(site_info) == 6:
        name = site_info[1] + ": " + site_info[2]
    if len(site_info) == 7:
        name = site_info[1] + ": " + site_info[2] + " " +site_info[3]
        
    # Get date and time
    if len(site_info) == 5:
        date = site_info[2]
        time = site_info[3]
    if len(site_info) == 6:
        date = site_info[3]
        time = site_info[4]
    if len(site_info) == 7:
        date = site_info[4]
        time = site_info[5]
     
    # Get lat and lon
    file_lines = open_file_and_split_into_lines(file_in)
    latlon = file_lines[3].split()
    lat = ""
    lon = ""
    for i, v in enumerate(latlon):
        if i == 7:
            ln = float(v.strip(","))
            lon = '{:.5f}'.format(ln)
        if i == 8:
            lt = float(v.strip(","))
            lat = '{:.5f}'.format(lt)
            
    # Get initial altitude
    alt_line = file_lines[3].replace(" ","").split(",")
    altitude = float(alt_line[6].rstrip())
    
    #########################
    
    # Extract data header and data into a dictionary and then a data frame
    data_d = pd.read_csv(os.path.join(directory_in, file_in), sep="\s{1,}", engine="python", header=12, skiprows=[13,14], usecols=["Time", "Alt", "spd", "dir", "Ucmp", "Vcmp", "Qp", "Qu", "Qv"]).to_dict(orient="list")
    data_df = pd.DataFrame.from_dict(data_d, orient='columns').astype(float).sort_index()  # convert dictionary to a data frame with float numbers

    # Format numbers to varying decimal places and get other data into lists
    h_temp = ["%.1f"%item for item in data_df["Alt"].values.tolist()]
    ws_temp = ["%.1f"%item for item in data_df["spd"].values.tolist()]
    wd_temp = ["%.1f"%item for item in data_df["dir"].values.tolist()]
    u_temp = ["%.1f"%item for item in data_df["Ucmp"].values.tolist()]
    v_temp = ["%.1f"%item for item in data_df["Vcmp"].values.tolist()]
    time_temp = data_df["Time"].values.tolist()
    qp_temp = data_df["Qp"].values.tolist()
    qu_temp = data_df["Qu"].values.tolist()
    qv_temp = data_df["Qv"].values.tolist()
    
    # Create new variables, put in good data, and replace bad data values with invalid value: "-9999"
    h = []
    ws = []
    wd = []
    u = []
    v = []      
    for ind in range(len(data_df)):
        # If wind speed is 0, set wind direction to -9999
        if float(ws_temp[ind]) == 0.00:
            wd_temp[ind] = invalid_value
            
        # Get initial values (sometimes these are flagged bad, but then this invalidates all initial conditions)  
        if ind == 0:
            if time_temp[ind] < 0:
                h.append("{0:>8s}".format(invalid_value))
                ws.append("{0:>11s}".format(invalid_value))
                wd.append("{0:>8s}".format(invalid_value))
                u.append("{0:>6s}".format(invalid_value))
                v.append("{0:>7s}".format(invalid_value))

            if time_temp[ind] >= 0:
                h.append("{0:>8s}".format(str(h_temp[ind])))  # this is the only one that usually has a value

            # If values are not missing, retain those values     
            if time_temp[ind] >= 0 and "999" not in ws_temp[ind]:
                ws.append("{0:>11s}".format(str(ws_temp[ind])))  
                
            if time_temp[ind] >= 0 and wd_temp[ind] == invalid_value:
                wd.append("{0:>8s}".format(str(wd_temp[ind])))                    
            if time_temp[ind] >= 0 and wd_temp[ind] != invalid_value and "999" not in wd_temp[ind]:
                wd.append("{0:>8s}".format(str(wd_temp[ind])))
                
            if time_temp[ind] >= 0 and "9999" not in u_temp[ind]:
                u.append("{0:>6s}".format(str(u_temp[ind])))
                
            if time_temp[ind] >= 0 and "9999" not in v_temp[ind]:
                v.append("{0:>7s}".format(str(v_temp[ind])))  
                
            # If values are missing, get the next values for the initial conditions, unless they still have bad values
            if time_temp[ind] >= 0 and "999" in ws_temp[ind] and "999" not in ws_temp[ind+1]:
                ws.append("{0:>11s}".format(str(ws_temp[ind+1])))
            if time_temp[ind] >= 0 and "999" in ws_temp[ind] and "999" in ws_temp[ind+1]:
                ws.append("{0:>11s}".format(invalid_value))
                
            if time_temp[ind] >= 0 and wd_temp[ind] != invalid_value and "999" in wd_temp[ind] and "999" not in wd_temp[ind+1]:
                wd.append("{0:>8s}".format(str(wd_temp[ind+1])))
            if time_temp[ind] >= 0 and wd_temp[ind] != invalid_value and "999" in wd_temp[ind] and "999" in wd_temp[ind+1]:
                wd.append("{0:>8s}".format(invalid_value))
                
            if time_temp[ind] >= 0 and "9999" in u_temp[ind] and "9999" not in u_temp[ind+1]:
                u.append("{0:>6s}".format(str(u_temp[ind+1])))
            if time_temp[ind] >= 0 and "9999" in u_temp[ind] and "9999" in u_temp[ind+1]:
                u.append("{0:>6s}".format(invalid_value)) 
                                 
            if time_temp[ind] >= 0 and "9999" in v_temp[ind] and "9999" not in v_temp[ind+1]:
                v.append("{0:>7s}".format(str(v_temp[ind+1])))
            if time_temp[ind] >= 0 and "9999" in v_temp[ind] and "9999" in v_temp[ind+1]:
                v.append("{0:>7s}".format(invalid_value)) 
                
        # For the rest of the data, add "invalid value" (-9999) if QC flags are missing (9) or bad (3)
        elif ind != 0:
            if qp_temp[ind] == 9 or qp_temp[ind] == 3 or "99999" in h_temp[ind]:
                h.append("{0:>8s}".format(invalid_value))
            else:
                h.append("{0:>8s}".format(str(h_temp[ind])))
                                
            if qu_temp[ind] == 9 or qu_temp[ind] == 3 or qv_temp[ind] == 9 or qv_temp[ind] == 3:
                ws.append("{0:>11s}".format(invalid_value))
                wd.append("{0:>8s}".format(invalid_value))
            else:
                ws.append("{0:>11s}".format(str(ws_temp[ind])))
                wd.append("{0:>8s}".format(str(wd_temp[ind])))
            
            if qu_temp[ind] == 9 or qu_temp[ind] == 3:
                u.append("{0:>6s}".format(invalid_value))
            else:
                u.append("{0:>6s}".format(str(u_temp[ind])))            
            
            if qv_temp[ind] == 9 or qv_temp[ind] == 3:
                v.append("{0:>7s}".format(invalid_value))
            else:
                v.append("{0:>7s}".format(str(v_temp[ind])))
                                    
    ########################                

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
    
    #########################
    
    # Add file_name and data to a dictionary which will then be printed out to text files
    uv_dict = {}
  
    file_in = sounding_file_dict["file_in"]
    file_out = file_in.replace("EOL", "UV")  # create output file name
    
    whole_file = site_header + "\n" + "---------------------------------------------" + "\n" + data_header + "\n" + sounding_file_dict["data"]

    uv_dict.update({file_out: whole_file}) # append file name (key) and data (value) to dictionary
           
    return uv_dict
    
#########################
       
def create_directory_out(directory_out):  # Check if directory exists, and if not, make it
    if not os.path.exists(directory_out):
        os.makedirs(directory_out)

#########################
    
def write_to_uv_files(dictionary):  # Write dictionary (uv_dict) items to files
    for name, data in dictionary.items():
        with open(os.path.join(directory_out, name), "w+") as f:
            f.write(data)
                         
#############################################################################
    
files_to_process = get_files_from_directory(directory_in)
create_directory_out(directory_out)

for file in files_to_process:
    sounding_file_dict = parse_info_from_eol_file(file)
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