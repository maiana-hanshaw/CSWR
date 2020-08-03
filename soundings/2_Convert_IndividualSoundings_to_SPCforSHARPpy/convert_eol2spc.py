### NAME:  convert_eol2spc.py

### MODIFICATION HISTORY:  Written by Maiana Hanshaw for Python (03/22/2020);

### PURPOSE:  To read in atmospheric sounding data in "EOL" file format and
#             output into "SPC" file format, which SHARPpy can read and simulate.

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

##   OUTGOING data needs to be in the "SPC" file format as shown below:

#%TITLE%
# SCOUT1   181110/1659 -31.72817,-63.84490
# 
#   LEVEL       HGHT       TEMP       DWPT       WDIR       WSPD
#-------------------------------------------------------------------
#%RAW%
#  963.20,    311.40,     35.00,     19.34,    196.00,     13.61
#  962.80,    315.00,     34.26,     18.68,    196.10,     13.63
#%END%

## More restrictions:   - cannot have an initial pressure of -9999
#                       - cannot have duplicate values of height or pressure
#                       - height cannot be decreasing, and pressure cannot be increasing
#                       - cannot have a space in site/vehicle name in header

### QUALITY CONTROL FLAGS:  SPC files need bad data to be in the format "-9999" ==> INVALID VALUE
#       Qp = Pressure
#       Qt = Temp
#       Qrh = Relative Humidity
#       Qu = Wind-u
#       Qv = Wind-v

#       2 = questionable/maybe - including these values for now
#       3 = BAD
#       9 = MISSING

###############################################################################

import os  # operating system library
import pandas as pd  # pandas library for dictionary and data frames
import re  # regular expressions library

###### UPDATE THIS ######
directory_in = "C:/Users/Maiana/Downloads/Soundings/RELAMPAGO/CSU/EOL_Files"  # location of "EOL" sounding data files
directory_out = "C:/Users/Maiana/Downloads/Soundings/RELAMPAGO/CSU/SPC_Files"  # location to output "SPC" sounding data files
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

########################
    
def pressure_decreasing(pressure, index, p):    
    lower = True
    if invalid_value not in pressure:        
        if index != 0:
            previous_pressure = p[index - 1]           
            if invalid_value in previous_pressure:
                lower = pressure_decreasing(pressure, index -1, p)
            else:
                lower = pressure < previous_pressure                
    return lower

########################

def parse_info_from_eol_file(file_in):

    print(file_in)  
     
    # Extract site info for site header from file name
    site_info = re.split(r'[_.\s]\s*', file_in)
 
    # Get site id/name
    if len(site_info) == 5:
        name = site_info[1]
    if len(site_info) == 6:
        name = site_info[1] + ":" + site_info[2]
    if len(site_info) == 7:
        name = site_info[1] + ":" + site_info[2] + "_" +site_info[3]
        
    # Get date and time
    if len(site_info) == 5:
        d = site_info[2]
        date = d[2:9]
        time = site_info[3]
    if len(site_info) == 6:
        d = site_info[3]
        date = d[2:9]
        time = site_info[4]
    if len(site_info) == 7:
        d = site_info[4]
        date = d[2:9]
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

    ########################

    # Extract data header and data into a dictionary and then a data frame
    data_d = pd.read_csv(os.path.join(directory_in, file_in), sep="\s{1,}", engine="python", header=12, skiprows=[13,14], usecols=["Time", "Press", "Alt", "Temp", "Dewpt", "dir", "spd", "Qp", "Qt", "Qrh", "Qu", "Qv"]).to_dict(orient="list")
    data_df = pd.DataFrame.from_dict(data_d, orient='columns').astype(float).sort_index()  # convert dictionary to a data frame with float numbers

    # Format numbers to varying decimal places and get other data into lists
    p_temp = ["%.2f"%item for item in data_df["Press"].values.tolist()]
    h_temp = ["%.2f"%item for item in data_df["Alt"].values.tolist()]
    t_temp = ["%.2f"%item for item in data_df["Temp"].values.tolist()]
    dp_temp = ["%.2f"%item for item in data_df["Dewpt"].values.tolist()]
    wd_temp = ["%.2f"%item for item in data_df["dir"].values.tolist()]
    ws_temp = data_df["spd"].values.tolist()  # will be formatted later after converting to knots
    time_temp = data_df["Time"].values.tolist()
    qp_temp = data_df["Qp"].values.tolist()
    qt_temp = data_df["Qt"].values.tolist()
    qrh_temp = data_df["Qrh"].values.tolist()
    qu_temp = data_df["Qu"].values.tolist()
    qv_temp = data_df["Qv"].values.tolist()
    
    # Create new variables, put in good data, and replace bad data values with invalid value: "-9999"
    p = []
    h = []
    t = []
    dp = []
    wd = []
    ws = []
    for ind in range(len(data_df)):
        # If wind speed is 0, set wind direction to -9999
        if float(ws_temp[ind]) == 0.00:
            wd_temp[ind] = invalid_value

        # Get initial values (sometimes these are flagged bad, but then this invalidates all initial conditions)     
        if ind == 0:
            if time_temp[ind] < 0:
                h.append("{0:>10s}".format(invalid_value))
                p.append("{0:>8s}".format(invalid_value))
                t.append("{0:>10s}".format(invalid_value))
                dp.append("{0:>10s}".format(invalid_value))
                wd.append("{0:>10s}".format(invalid_value))
                ws.append("{0:>10s}".format(invalid_value))
            
            if time_temp[ind] >= 0:
                h.append("{0:>10s}".format(str(h_temp[ind])))  # this is the only one that usually has a value
                
            # If values are not missing, retain those values    
            if time_temp[ind] >= 0 and "9999" not in p_temp[ind]:
                p.append("{0:>8s}".format(str(p_temp[ind])))
                
            if time_temp[ind] >= 0 and "999" not in t_temp[ind]:
                t.append("{0:>10s}".format(str(t_temp[ind])))
                
            if time_temp[ind] >= 0 and "999" not in dp_temp[ind]:
                dp.append("{0:>10s}".format(str(dp_temp[ind])))  
                
            if time_temp[ind] >= 0 and wd_temp[ind] == invalid_value:
                wd.append("{0:>10s}".format(str(wd_temp[ind])))                    
            if time_temp[ind] >= 0 and wd_temp[ind] != invalid_value and "999" not in wd_temp[ind]:
                wd.append("{0:>10s}".format(str(wd_temp[ind])))
                
            if time_temp[ind] >= 0 and ws_temp[ind] != 999:
                ws_value = '{:.2f}'.format(float(ws_temp[ind]) * 1.94384)  # convert wind speed to knots
                ws.append("{0:>10s}".format(str(ws_value)))

            # If values are missing, get the next values for the initial conditions, unless they still have bad values
            if time_temp[ind] >= 0 and "9999" in p_temp[ind] and "9999" not in p_temp[ind+1]:
                p.append("{0:>8s}".format(str(p_temp[ind+1])))
            if time_temp[ind] >= 0 and "9999" in p_temp[ind] and "9999" in p_temp[ind+1]:
                p.append("{0:>8s}".format(invalid_value))                
                
            if time_temp[ind] >= 0 and "999" in t_temp[ind] and "999" not in t_temp[ind+1]:
                t.append("{0:>10s}".format(str(t_temp[ind+1])))
            if time_temp[ind] >= 0 and "999" in t_temp[ind] and "999" in t_temp[ind+1]:
                t.append("{0:>10s}".format(invalid_value))                
                
            if time_temp[ind] >= 0 and "999" in dp_temp[ind] and "999" not in dp_temp[ind+1]:
                dp.append("{0:>10s}".format(str(dp_temp[ind+1]))) 
            if time_temp[ind] >= 0 and "999" in dp_temp[ind] and "999" in dp_temp[ind+1]:
                dp.append("{0:>10s}".format(invalid_value))                 
                 
            if time_temp[ind] >= 0 and wd_temp[ind] != invalid_value and "999" in wd_temp[ind] and "999" not in wd_temp[ind+1]:
                wd.append("{0:>10s}".format(str(wd_temp[ind+1])))  
            if time_temp[ind] >= 0 and wd_temp[ind] != invalid_value and "999" in wd_temp[ind] and "999" in wd_temp[ind+1]:
                wd.append("{0:>10s}".format(invalid_value))                  
                
            if time_temp[ind] >= 0 and ws_temp[ind] == 999 and ws_temp[ind+1] != 999:
                ws_value = '{:.2f}'.format(float(ws_temp[ind+1]) * 1.94384)  # convert wind speed to knots
                ws.append("{0:>10s}".format(str(ws_value)))  
            if time_temp[ind] >= 0 and ws_temp[ind] == 999 and ws_temp[ind+1] == 999:
                ws.append("{0:>10s}".format(invalid_value))                

        # For the rest of the data, add "invalid value" (-9999) if QC flags are missing (9) or bad (3)
        elif ind != 0:
            if qp_temp[ind] == 9: 
                p.append("{0:>8s}".format(invalid_value))
            else:
                p.append("{0:>8s}".format(str(p_temp[ind])))
                
            if qp_temp[ind] == 9 or qp_temp[ind] == 3 or "99999" in h_temp[ind]: 
                h.append("{0:>10s}".format(invalid_value))
            else:
                h.append("{0:>10s}".format(str(h_temp[ind])))                

            if qt_temp[ind] == 9 or qt_temp[ind] == 3:
                t.append("{0:>10s}".format(invalid_value))
            else:
                t.append("{0:>10s}".format(str(t_temp[ind])))            
            
            if qrh_temp[ind] == 9 or qrh_temp[ind] == 3 or qt_temp[ind] == 9 or qt_temp[ind] == 3:
                dp.append("{0:>10s}".format(invalid_value))
            else:
                dp.append("{0:>10s}".format(str(dp_temp[ind])))
                
            if qu_temp[ind] == 9 or qu_temp[ind] == 3 or qv_temp[ind] == 9 or qv_temp[ind] == 3:
                wd.append("{0:>10s}".format(invalid_value))
                ws.append("{0:>10s}".format(invalid_value))
            else:
                wd.append("{0:>10s}".format(str(wd_temp[ind])))
                ws_value = '{:.2f}'.format(float(ws_temp[ind]) * 1.94384)  # convert wind speed to knots
                ws.append("{0:>10s}".format(str(ws_value))) 
                
    ########################                

    # Check if pressure values are decreasing, and if not, make values -9999
    for index in range(len(data_df)):
        lower = pressure_decreasing(p[index], index, p)
    
        if not lower:
            p[index] = "{0:>10s}".format(invalid_value)
            h[index] = "{0:>10s}".format(invalid_value)
            t[index] = "{0:>10s}".format(invalid_value)
            dp[index] = "{0:>10s}".format(invalid_value)
            wd[index] = "{0:>10s}".format(invalid_value)
            ws[index] = "{0:>10s}".format(invalid_value)
    
    # Check if height values are increasing, and if not, make values -9999
    for index in range(len(data_df)):
        higher = height_increasing(h[index], index, h, altitude)
    
        if not higher:
            h[index] = "{0:>10s}".format(invalid_value)
            t[index] = "{0:>10s}".format(invalid_value)
            dp[index] = "{0:>10s}".format(invalid_value)
            wd[index] = "{0:>10s}".format(invalid_value)
            ws[index] = "{0:>10s}".format(invalid_value)
          
    ########################

    # Put the data together
    spc_data_list = []  # create empty list to fill with correctly spaced data    

    for ind in range(len(data_df)):
        if "-9999" in p[ind]:
            continue
        if p[ind] == p[ind-1]:
            continue         
        pressure = p[ind]
        height = h[ind]
        temp = t[ind]
        dwpt = dp[ind]
        wdir = wd[ind]
        wspd = ws[ind] 

        spc_string = "{},{},{},{},{},{}".format(pressure, height, temp, dwpt, wdir, wspd)  # create the new string for each row
        spc_data_list.append(spc_string)  # add each row into the new list    
       
    spc_data = "\n".join(spc_data_list)  # join all the elements together again into a string

    ########################
    
    # Get info that could be problematic
    flag = ""
    if spc_data_list != []:
        h_line = spc_data_list[0].split()
        h_init = float(h_line[1].strip(","))
    else:
        h_init = altitude
        flag = "FILE COMPLETELY EMPTY"
        
    # Add a problem flag if the pressure difference is > 20mb
    missing_interpolated = ""    
    pressure = []
    for ind in range(len(spc_data_list)):
        line = spc_data_list[ind].split()
        pressure.append(float(line[0].strip(",")))
     
    for ind in range(len(pressure)):
        if ind != 0:
            pressure_current = pressure[ind]
            pressure_previous = pressure[ind-1]
            pressure_diff = pressure_current - pressure_previous
            if pressure_diff <= -20:
                diff_string = '{:.1f}'.format(pressure_diff)
                missing_interpolated += "PROBLEM (Missing/Interpolated) = " + "Diff: " + diff_string

    ########################
        
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
    sounding_file_dict["missing"] = missing_interpolated
    sounding_file_dict["data"] = spc_data
    
    return sounding_file_dict

#########################

def output_to_spc_format(sounding_file_dict):

    # Construct site header
    site_header = " {}   {}/{} {},{}".format(sounding_file_dict["site_name"], sounding_file_dict["date"], sounding_file_dict["time"], sounding_file_dict["lat"], sounding_file_dict["lon"])

    # Construct data header
    pressure = "LEVEL"
    height = "HGHT"
    temp = "TEMP"
    dwpt = "DWPT"
    wdir = "WDIR"
    wspd = "WSPD"

    data_header = "   {}       {}       {}       {}       {}       {}".format(pressure, height, temp, dwpt, wdir, wspd)

    ########################

    # Add file_name and data to a dictionary which will then be printed out to text files
    spc_dict = {}
    
    file_in = sounding_file_dict["file_in"]
    file_out = file_in.replace("EOL", "SPC")  # create output file name

    whole_file = ("%TITLE%" + "\n" + site_header + "\n\n" + data_header + "\n"
                  + "-------------------------------------------------------------------"
                  + "\n" + "%RAW%" + "\n" + sounding_file_dict["data"] + "\n" + "%END%")
  
    spc_dict.update({file_out: whole_file}) # append file name (key) and data (value) to dictionary
    
    return spc_dict

#########################
       
def create_directory_out(directory_out):  # Check if directory exists, and if not, make it
    if not os.path.exists(directory_out):
        os.makedirs(directory_out)

#########################
    
def write_to_spc_files(dictionary):  # Write dictionary items to files
    for name, data in dictionary.items():
        with open(os.path.join(directory_out, name), "w+") as f:
            f.write(data)

#############################################################################
    
files_to_process = get_files_from_directory(directory_in)
create_directory_out(directory_out)

for file in files_to_process:
    sounding_file_dict = parse_info_from_eol_file(file)
    spc_dict = output_to_spc_format(sounding_file_dict)

    # Incrementally append problem file names to a text file
    problem = ""
    alt_diff = sounding_file_dict["h_init"] - sounding_file_dict["alt"]
    if alt_diff >= 5:
        alt_diff_string = '{:.1f}'.format(alt_diff)
        problem += "PROBLEM (Alt. Diff >= 5) = " + alt_diff_string
        
    if sounding_file_dict["flag"] != "":
        problem += "PROBLEM = " + sounding_file_dict["flag"]
        
    if sounding_file_dict["missing"] != "":
        problem += sounding_file_dict["missing"]
    
    if problem != "":
        with open(os.path.join(directory_out, "Problem_Files.txt"), "a+") as f:            
            f.seek(0)  # move cursor to the start of file            
            data = f.read(100) # if file is not empty then append '\n'
            if len(data) > 0:
                f.write("\n")
            # Append text to the end of the file
            f.write(file + ": " + problem)
           
    # Write converted files to text files
    write_to_spc_files(spc_dict)

#############################################################################