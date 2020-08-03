### NAME:  convert_hgt2spc.py

### MODIFICATION HISTORY:  Written by Maiana Hanshaw for Python (03/22/2020)

### PURPOSE:  To read in CSWR quality-controlled atmospheric sounding data in "HGT" file
#            format and output into "SPC" file format, which SHARPpy can read and simulate.

### RESTRICTIONS:
##   INCOMING data needs to be in the "Hgt" file format as shown below:

#   STN      DATE   GMT   HTS        LAT         LON
#SCOUT1  20181110  1659   311  -31.72817   -63.84490
#NLVL =2137
#       P      HT      TC      TD     DIR     SPD  QP QH QT QD QW        LON       LAT
#   963.2   311.4   35.00   19.34  196.00    7.00   1  1  1  1  1  -63.84490 -31.72817
#   962.8   315.0   34.26   18.68  196.10    7.01   1  1  1  1  1  -63.84489 -31.72820

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

### QUALITY CONTROL FLAGS:  SPC files need bad data to be in the format "-9999.00"
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

###### UPDATE THIS ######
directory_in = "C:/Users/Maiana/Downloads/Soundings/RELAMPAGO/HGT_Files"  # location of "Hgt" sounding data files
directory_out = "C:/Users/Maiana/Downloads/Soundings/RELAMPAGO/SPC_Files"  # location to output "SPC" sounding data files
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

########################
  
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

def parse_info_from_hgt_file(file_in):
        
    print(file_in)
       
    # Extract vehicle info for vehicle header from file name
    vehicle_info = re.split(r'[_.\s]\s*', file_in)
 
    # Get vehicle id/name
    vehicle = vehicle_info[2]
        
    # Get date and time
    d = vehicle_info[1]
    date = d[2:9]
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
    data_d = pd.read_csv(os.path.join(directory_in, file_in), sep="\s{1,}", engine="python", header=3, usecols=["P", "HT", "TC", "TD", "DIR", "SPD", "QP", "QH", "QT", "QD", "QW"]).to_dict(orient="list")
    data_df = pd.DataFrame.from_dict(data_d, orient='columns').astype(float).sort_index()  # convert dictionary to a data frame with float numbers

    # Format numbers to 2 decimal places
    p_temp = ["%.2f"%item for item in data_df["P"].values.tolist()]
    h_temp = ["%.2f"%item for item in data_df["HT"].values.tolist()]
    t_temp = ["%.2f"%item for item in data_df["TC"].values.tolist()]
    dp_temp = ["%.2f"%item for item in data_df["TD"].values.tolist()]
    wd_temp = ["%.2f"%item for item in data_df["DIR"].values.tolist()]
    ws_temp = data_df["SPD"].values.tolist()  # will be formatted later after converting to knots
    
    # Create new variables, put in good data, and replace bad data values with "-9999"
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
            
        # Add "-9999" if QC flags are missing (9), visually bad (5), or objectively bad (4)
        if data_df["QP"][ind] == 9 or data_df["QP"][ind] == 5 or data_df["QP"][ind] == 4:
            p.append("{0:>8s}".format(invalid_value))
        else:
            p.append("{0:>8s}".format(str(p_temp[ind])))
            
        if data_df["QH"][ind] == 9 or data_df["QH"][ind] == 5 or data_df["QH"][ind] == 4:
            h.append("{0:>10s}".format(invalid_value))
        else:
            h.append("{0:>10s}".format(str(h_temp[ind])))        
            
        if data_df["QT"][ind] == 9 or data_df["QT"][ind] == 5 or data_df["QT"][ind] == 4:
            t.append("{0:>10s}".format(invalid_value))
        else:
            t.append("{0:>10s}".format(str(t_temp[ind])))
            
        if data_df["QD"][ind] == 9 or data_df["QD"][ind] == 5 or data_df["QD"][ind] == 4:
            dp.append("{0:>10s}".format(invalid_value))
        else:
            dp.append("{0:>10s}".format(str(dp_temp[ind])))            
         
        if data_df["QW"][ind] == 9 or data_df["QW"][ind] == 5 or data_df["QW"][ind] == 4:
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
            p[index] = "{0:>10s}".format(invalid_value)
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
        
    h_flag_0 = data_df["QH"][0]
    h_flag_100 = data_df["QH"][100]
    
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
    sounding_file_dict["missing"] = missing_interpolated
    sounding_file_dict["data"] = spc_data
    
    return sounding_file_dict    
        
#########################
    
def output_to_spc_format(sounding_file_dict):

    # Construct vehicle header
    vehicle_header = " {}   {}/{} {},{}".format(sounding_file_dict["vehicle_name"], sounding_file_dict["date"], sounding_file_dict["time"], sounding_file_dict["lat"], sounding_file_dict["lon"])

    # Construct data header in "SPC" format
    pressure = "LEVEL"
    height = "HGHT"
    temp = "TEMP"
    dewpt = "DWPT"
    wdir = "WDIR"
    wspd = "WSPD"

    data_header = "   {}       {}       {}       {}       {}       {}".format(pressure, height, temp, dewpt, wdir, wspd)

    ######################## 
    
    # Add file_name and data to a dictionary which will then be printed out to text files    
    spc_dict = {}
   
    file_in = sounding_file_dict["file_in"]
    file_out = file_in.replace("Hgt", "SPC") + ".txt"  # create output file name

    whole_file = ("%TITLE%" + "\n" + vehicle_header + "\n\n" + data_header + "\n"
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
    sounding_file_dict = parse_info_from_hgt_file(file)
    spc_dict = output_to_spc_format(sounding_file_dict)
    
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