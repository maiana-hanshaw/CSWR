### NAME:  convert_uah2spc.py

### MODIFICATION HISTORY:  Written by Maiana Hanshaw for Python (03/22/2020);

### PURPOSE:  To read in atmospheric sounding data from UAH, which is in its own format,
#             and output into "SPC" file format, which SHARPpy can read and simulate.

### RESTRICTIONS:
##   INCOMING UAH data needs to be in the format as shown below:

#VORTEX-SE 2017 UAH Radiosonde Data
#20170328, 0051 UTC, Brownsferry, AL, 201 m
#latitude (deg), longitude (deg),time (sec),height (m MSL),pressure(mb),temp (deg C),RH (%),dewpoint (deg C),Calculated wind speed (kts),Calculated wind direction (deg)
#34.73705, -87.12219, 0:52:2, 223.0, 984.3, 17.13, 86.1, 14.83, 8.2, 127 
#34.73712, -87.1223, 0:52:5, 242.0, 982.16, 17.43, 84.85, 14.9, 8.0, 116 
#34.73717, -87.12242, 0:52:8, 261.0, 979.9, 17.61, 83.4, 14.82, 14.2, 165 
#%END%

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

### SPC files need bad data to be in the format "-9999", although the UAH data does not have QC flags
### Although no flags exist in the UAH data, I have attempted to add some based on info from the log notes

###############################################################################

import os  # operating system library
import pandas as pd  # pandas library for dictionary and data frames
import re  # regular expressions library
import math # math library

###### UPDATE THIS ######
directory_in = "C:/Users/Maiana/Downloads/Soundings/VSE-2017/Data/UAH"  # location of UAH sounding data files
directory_out = "C:/Users/Maiana/Downloads/Soundings/VSE-2017/Data/UAH/SPC_Files"  # location to output "SPC" sounding data files
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
    
def calculate_dewpoint(t_value, rh_value):
    dewpoint = 243.04*(math.log(rh_value/100)+((17.625*t_value)/(243.04+t_value)))/(17.625-math.log(rh_value/100)-((17.625*t_value)/(243.04+t_value)))
    return dewpoint

#########################

def parse_info_from_uah_file(file_in):

    print(file_in)  
     
    # Extract site info from file name for both the "SPC" format site header and the new file name
    site_info = re.split(r'[_.\s]\s*', file_in)
 
    # Get site id/name
    inst_id = site_info[1]
    location = site_info[4]
    name = inst_id + ":" + location
        
    # Get date and time
    dt = site_info[3]
    file_name_date = dt[0:8]
    date = dt[2:8]
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
    if "height (m MSL)"  in file_lines[2] and "dewpoint (deg C)" in file_lines[2] and "Calculated" in file_lines[2]:
        col_headers = ["height (m MSL)", "pressure(mb)", "temp (deg C)", "dewpoint (deg C)", "Calculated wind speed (kts)", "Calculated wind direction (deg)"]
    elif "height (m MSL)"  in file_lines[2] and "dewpoint (deg C)" in file_lines[2] and "Calculated" not in file_lines[2]:
        col_headers = ["height (m MSL)", "pressure(mb)", "temp (deg C)", "dewpoint (deg C)", "wind speed (kts)", "wind direction (deg)"]
    elif "height (m AGL)" in file_lines[2]:
        col_headers = ["height (m AGL)", "pressure(mb)", "temp (deg C)", "dewpoint (deg C)", "wind speed (kts)", "wind direction (deg)"]
    elif "height (m MSL)" in file_lines[2] and "dewpoint (deg C)" not in file_lines[2]:
        col_headers = ["height (m MSL)", "pressure(mb)", "temp (deg C)", "RH (%)", "wind speed (kts)", "wind direction (deg)"]

    # Extract data header and data into a dictionary and then a data frame
    data_d = pd.read_csv(os.path.join(directory_in, file_in), sep=",", engine="python", header=2, skipfooter=1, usecols=col_headers).to_dict(orient="list")
    data_df = pd.DataFrame.from_dict(data_d, orient='columns').astype(float).sort_index()  # convert dictionary to a data frame with float numbers

    # Standardize column headers   
    if "Calculated" in file_lines[2]:
        data_df.columns = ["Height (masl)", "Pressure (mb)", "Temp (C)", "DWPT (C)", "WSPD (kts)", "WDIR (deg)"]
    elif "height (m MSL)" in file_lines[2] and "dewpoint (deg C)" in file_lines[2] and "Calculated" not in file_lines[2]:
        data_df.columns = ["Height (masl)", "Pressure (mb)", "Temp (C)", "DWPT (C)", "WSPD (kts)", "WDIR (deg)"]        
    elif "height (m AGL)" in file_lines[2]:
        data_df["height (m AGL)"] += altitude  # add initial altitude to height values
        data_df.columns = ["Height (masl)", "Pressure (mb)", "Temp (C)", "DWPT (C)", "WSPD (kts)", "WDIR (deg)"]
    # This is a complicated one that does not have dewpoint, so it needs to be calculated from RH
    elif "height (m MSL)" in file_lines[2] and "dewpoint (deg C)" not in file_lines[2]:
        data_df.columns = ["Height (masl)", "Pressure (mb)", "Temp (C)", "RH (%)", "WSPD (kts)", "WDIR (deg)"]
        
    # Get data into lists
    h_list = data_df["Height (masl)"].values.tolist()
    p_list = data_df["Pressure (mb)"].values.tolist()  
    t_list = data_df["Temp (C)"].values.tolist()
    ws_list = data_df["WSPD (kts)"].values.tolist() 
    wd_list = data_df["WDIR (deg)"].values.tolist()
    if "dewpoint (deg C)" in file_lines[2]:
        dp_list = data_df["DWPT (C)"].values.tolist()
    elif "dewpoint (deg C)" not in file_lines[2]:
        rh_list = data_df["RH (%)"].values.tolist()
        rh_temp = ["%.2f"%item for item in rh_list]
        dp_list = []
        for ind in range(len(data_df)):
            dp_value = calculate_dewpoint(t_list[ind], rh_list[ind])
            dp_list.append(dp_value)

    ########################        
        
    # Format numbers to varying decimal places
    p_temp = ["%.2f"%item for item in p_list]    
    h_temp = ["%.2f"%item for item in h_list]
    t_temp = ["%.2f"%item for item in t_list]
    dp_temp = ["%.2f"%item for item in dp_list]
    wd_temp = ["%.2f"%item for item in wd_list]
    ws_temp = ["%.2f"%item for item in ws_list] 
    
    # Create new variables and put in good data
    p = []
    h = []
    t = []
    dp = []
    wd = []
    ws = []
    flag = ""
    for ind in range(len(data_df)):
        
        # Correct some bad data as noted in the log notes
        ## For VSE-2017
        if file_in == "upperair.UAH_Sonde.201703271505.Huntsville_AL.txt":
            if ind == 0:
                p_temp[0] = "990.80" # launch pressure taken from 1700 sounding at this site, as it was previously incorrectly SL pressure
            else:
                p_temp[ind] = invalid_value
            flag = "BAD PRESSURES"
            
        # If wind speed is 0, set wind direction to -9999
        if float(ws_temp[ind]) == 0.00:
            wd_temp[ind] = invalid_value
                
        # Add "-9999" if data is missing (-9999.0)
        if invalid_value in p_temp[ind]:
            p.append("{0:>8s}".format(invalid_value))
        else:
            p.append("{0:>8s}".format(str(p_temp[ind])))
            
        if invalid_value in h_temp[ind]:
            h.append("{0:>10s}".format(invalid_value))
        else:
            h.append("{0:>10s}".format(str(h_temp[ind])))        
            
        if invalid_value in t_temp[ind]:
            t.append("{0:>10s}".format(invalid_value))
        else:
            t.append("{0:>10s}".format(str(t_temp[ind])))
            
        if "dewpoint (deg C)" in file_lines[2]:
            if invalid_value in dp_temp[ind]:
                dp.append("{0:>10s}".format(invalid_value))
            else:
                dp.append("{0:>10s}".format(str(dp_temp[ind])))  
        elif "dewpoint (deg C)" not in file_lines[2]:
            if invalid_value in rh_temp[ind]:
                dp.append("{0:>10s}".format(invalid_value))
            else:
                dp.append("{0:>10s}".format(str(dp_temp[ind])))
                
        if invalid_value in wd_temp[ind]:
            wd.append("{0:>10s}".format(invalid_value))
        else:
            wd.append("{0:>10s}".format(str(wd_temp[ind])))
            
        if invalid_value in ws_temp[ind]:
            ws.append("{0:>10s}".format(invalid_value))
        else:
            ws.append("{0:>10s}".format(str(ws_temp[ind])))
            
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
            p[index] = "{0:>10s}".format(invalid_value)
            h[index] = "{0:>10s}".format(invalid_value)
            t[index] = "{0:>10s}".format(invalid_value)
            dp[index] = "{0:>10s}".format(invalid_value)
            wd[index] = "{0:>10s}".format(invalid_value)
            ws[index] = "{0:>10s}".format(invalid_value)
            
    # Sometimes the last wind value is super funky, so check it and make ws and wd -9999 if necessary
    for ind in range(len(data_df)):
        if ind == (len(data_df)-1):
            wind = ws[ind]
            previous_wind = ws[ind-1]
            if wind > previous_wind * 3:
                ws[ind] = "{0:>10s}".format(invalid_value)
                wd[ind] = "{0:>10s}".format(invalid_value)
            
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

    #########################
        
    # Get info that could be problematic 
    if spc_data_list != []:
        h_line = spc_data_list[0].split()
        h_init = float(h_line[1].strip(","))
    else:
        h_init = altitude
        flag += "FILE COMPLETELY EMPTY"
        
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
    sounding_file_dict["inst_id"] = inst_id
    sounding_file_dict["location"] = location
    sounding_file_dict["site_name"] = name
    sounding_file_dict["date"] = date
    sounding_file_dict["time"] = time
    sounding_file_dict["file_name_date"] = file_name_date
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

    # Construct data header in "SPC" format
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
  
    file_out = "SPC_{}_{}_{}_{}.txt".format(sounding_file_dict["inst_id"], sounding_file_dict["location"], sounding_file_dict["file_name_date"], sounding_file_dict["time"])  # create output file name

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
    sounding_file_dict = parse_info_from_uah_file(file)
    spc_dict = output_to_spc_format(sounding_file_dict)

    # Incrementally append problem file names to a text file
    problem = ""
    alt_diff = sounding_file_dict["h_init"] - sounding_file_dict["alt"]
    if alt_diff >= 5:
        alt_diff_string = '{:.1f}'.format(alt_diff)
        problem += "Problem (Alt. Diff >= 5) = " + alt_diff_string
         
    if sounding_file_dict["flag"] != "":
        problem += "Problem (Flag) = " + sounding_file_dict["flag"]
        
    if sounding_file_dict["missing"] != "":
        problem += sounding_file_dict["missing"]

    if problem != "":
        with open(os.path.join(directory_out, "Problem_Files_UAH.txt"), "a+") as f:            
            f.seek(0)  # move cursor to the start of file            
            data = f.read(100) # if file is not empty then append '\n'
            if len(data) > 0:
                f.write("\n")
            # Append text to the end of the file
            f.write(file + ": " + problem)
           
    # Write converted files to text files
    write_to_spc_files(spc_dict)

#############################################################################