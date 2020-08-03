"""
SHARPpy: Plotting a sounding with indices and a hodograph
================================================
"""
### NAME:  sharppy_process_soundings.py

### MODIFICATION HISTORY:  Original code provided as an example by SHARPpy creators.
#   Modified by Maiana Hanshaw (03/25/2020) to:
#       - read in multiple SPC files and batch process them
#       - output SKEW-Ts to a specific folder
#       - output indices to text files in a specific folder
#       - rename the files to our convention

###############################################################################

#import os  # operating system library
#import pandas as pd  # pandas library for dictionary and data frames
#import re  # regular expressions library

###### UPDATE THIS ######
directory_in = "C:/Users/Maiana/Downloads/Soundings/RELAMPAGO/CSU/SPC_Files"  # location of "SPC" sounding data files
directory_out_skewt = "C:/Users/Maiana/Downloads/Soundings/RELAMPAGO/CSU/SHARPpy/SkewTs"  # location to output SHARPpy Skew-Ts
directory_out_indices = "C:/Users/Maiana/Downloads/Soundings/RELAMPAGO/CSU/SHARPpy/Indices"  # location to output SHARPpy Indices
#########################

import os  # operating system library
from datetime import datetime

start_time = datetime.now()

def get_files_from_directory(directory_in):

    selected_files = []
    for root, dirs, files in os.walk(directory_in):
        if root == directory_in:
            for file in files:
                if "SPC" in file:
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

import warnings # Silence the warnings from SHARPpy
warnings.filterwarnings("ignore")
import sharppy.plot.skew as skew
from matplotlib.ticker import ScalarFormatter, MultipleLocator
from matplotlib.collections import LineCollection
import matplotlib.transforms as transforms
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import gridspec
from sharppy.sharptab import winds, utils, params, thermo, interp, profile
from sharppy.io.spc_decoder import SPCDecoder

def decode(filename):

    dec = SPCDecoder(filename)

    if dec is None:
        raise IOError("Could not figure out the format of '%s'!" % filename)

    # Returns the set of profiles from the file that are from the "Profile" class.
    profs = dec.getProfiles()
    stn_id = dec.getStnId()

    for k in list(profs._profs.keys()):
        all_prof = profs._profs[k]
        dates = profs._dates
        for i in range(len(all_prof)):
            prof = all_prof[i]
            new_prof = profile.create_profile(pres=prof.pres, hght=prof.hght, tmpc=prof.tmpc, dwpc=prof.dwpc, wspd=prof.wspd, \
                                              wdir=prof.wdir, strictQC=False, profile='convective', date=dates[i])
            return new_prof, dates[i], stn_id
        
#########################
       
def create_directory_out(directory_out):  # Check if directory exists, and if not, make it
    if not os.path.exists(directory_out):
        os.makedirs(directory_out)

#########################
      
# To plot a reduced number of wind barbs so that they are actually visible:        
def pressure_interval(p,u,v,upper,lower,spacing):

    intervals = list(range(upper,lower,spacing))
    ix = []
    for center in intervals:
        index = (np.abs(p-center)).argmin()
        if index not in ix:
            ix.append(index)

    return p[ix],u[ix],v[ix]

###############################################################################    

files_to_process = get_files_from_directory(directory_in)
create_directory_out(directory_out_skewt)
create_directory_out(directory_out_indices)

for file in files_to_process:

    FILENAME = os.path.join(directory_in, file)
    print("\n" + file) 
    
    #########################

    # Get lat and lon 
    file_lines = open_file_and_split_into_lines(FILENAME)
    latlon_line = file_lines[1].split()
    latlon = latlon_line[2].split(",")
    lat = latlon[0]
    lon = latlon[1]
    
    #########################

    prof, time, location = decode(FILENAME)
    end_time = datetime.now()
    print("Decode Function: {}".format(end_time - start_time))
  
    #########################
    
    # Bounds of the pressure axis 
    pb_plot=1050
    pt_plot=100
    dp_plot=10
    plevs_plot = np.arange(pb_plot,pt_plot-1,-dp_plot)
    # Open up the SPC text file with the data in columns
    file_title = file.strip("SPC_").strip(".txt").replace("_", " ")
    title = file_title + '   (Observed)'

    # Set up the figure in matplotlib.
    plt.ioff()
    fig = plt.figure(figsize=(14, 14))
    gs = gridspec.GridSpec(4,4, width_ratios=[1,5,1,1])
    ax = plt.subplot(gs[0:3, 0:2], projection='skewx')
    skew.draw_title(ax, title)
    ax.grid(True)
    plt.grid(True)

    # Plot the background variables
    presvals = np.arange(1000, 0, -10)

    ax.semilogy(prof.tmpc[~prof.tmpc.mask], prof.pres[~prof.tmpc.mask], 'r', lw=2)
    ax.semilogy(prof.dwpc[~prof.dwpc.mask], prof.pres[~prof.dwpc.mask], 'g', lw=2)
    ax.semilogy(prof.vtmp[~prof.dwpc.mask], prof.pres[~prof.dwpc.mask], 'r--')
    ax.semilogy(prof.wetbulb[~prof.dwpc.mask], prof.pres[~prof.dwpc.mask], 'c-')

    # Plot the parcel trace, but this may fail.  If it does so, inform the user.
    try:
        ax.semilogy(prof.mupcl.ttrace, prof.mupcl.ptrace, 'k--')
    except:
        print("Couldn't plot parcel traces...")

    # Highlight the 0 C and -20 C isotherms.
    l = ax.axvline(0, color='b', ls='--')
    l = ax.axvline(-20, color='b', ls='--')

    # Disables the log-formatting that comes with semilogy
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.set_yticks(np.linspace(100,1000,10))
    ax.set_ylim(1050,100)

    # Plot the hodograph data.
    inset_axes = skew.draw_hodo_inset(ax, prof)
    skew.plotHodo(inset_axes, prof.hght, prof.u, prof.v, color='r')

    #########################

    # Calculate fewer wind barbs and create sub-plots

    # Draw the wind barbs axis and everything that comes with it.
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.set_xlim(-50,50)
    ax2 = plt.subplot(gs[0:3,2])
    ax3 = plt.subplot(gs[3,0:3])
    skew.plot_wind_axes(ax2)
    #skew.plot_wind_barbs(ax2, prof.pres, prof.u, prof.v)  # all the wind barbs (usually too many to see pattern)

    # Reduce the number of data points to use for the wind barbs
    p_less, u_less, v_less = pressure_interval(prof.pres, prof.u, prof.v, 0, 1050, 25)
    skew.plot_wind_barbs(ax2, p_less, u_less, v_less)  

    srwind = params.bunkers_storm_motion(prof)
    gs.update(left=0.05, bottom=0.05, top=0.95, right=1, wspace=0.025)

    #########################

    # Calculate indices to be shown.
    p1km = interp.pres(prof, interp.to_msl(prof, 1000.))
    p3km = interp.pres(prof, interp.to_msl(prof, 3000.))
    p6km = interp.pres(prof, interp.to_msl(prof, 6000.))
    p8km = interp.pres(prof, interp.to_msl(prof, 8000.))
    p9km = interp.pres(prof, interp.to_msl(prof, 9000.))
    sfc = prof.pres[prof.sfc]
    sfc_1km_shear = winds.wind_shear(prof, pbot=sfc, ptop=p1km)
    sfc_3km_shear = winds.wind_shear(prof, pbot=sfc, ptop=p3km)
    sfc_6km_shear = winds.wind_shear(prof, pbot=sfc, ptop=p6km)
    sfc_8km_shear = winds.wind_shear(prof, pbot=sfc, ptop=p8km)
    sfc_9km_shear = winds.wind_shear(prof, pbot=sfc, ptop=p9km)
    srh3km = winds.helicity(prof, 0, 3000., stu = srwind[0], stv = srwind[1])
    srh1km = winds.helicity(prof, 0, 1000., stu = srwind[0], stv = srwind[1])
    scp = params.scp(prof.mupcl.bplus, prof.right_esrh[0], prof.ebwspd)
    stp_cin = params.stp_cin(prof.mlpcl.bplus, prof.right_esrh[0], prof.ebwspd, prof.mlpcl.lclhght, prof.mlpcl.bminus)
    stp_fixed = params.stp_fixed(prof.sfcpcl.bplus, prof.sfcpcl.lclhght, srh1km[0], utils.comp2vec(prof.sfc_6km_shear[0], prof.sfc_6km_shear[1])[1])
    ship = params.ship(prof)

    #########################

    # A routine to perform the correct formatting when writing the indices out to the figure.
    def fmt(value, fmt='int'):
        if fmt == 'int':
            try:
                val = int(value)
            except:
                val = str("M")
        else:
            try:
                val = round(value,1)
            except:
                val = "M"
        return val

    # Create a dictionary that is a collection of all of the indices we want.
    # The dictionary includes the index name, the actual value, and the units.
    indices = {'SBCAPE': [fmt(prof.sfcpcl.bplus), 'J/kg'],\
               'MLCAPE': [fmt(prof.mlpcl.bplus), 'J/kg'],\
               'MUCAPE': [fmt(prof.mupcl.bplus), 'J/kg'],\
               'MLLCL': [fmt(prof.mlpcl.lclhght), 'm AGL'],\
               'SBLCL': [fmt(prof.sfcpcl.lclhght), 'm AGL'],\
               '0-1 km SRH': [fmt(srh1km[0]), 'm2/s2'],\
               '0-3 km SRH': [fmt(srh3km[0]), 'm2/s2'],\
               '0-1 km Shear': [fmt(utils.comp2vec(sfc_1km_shear[0], sfc_1km_shear[1])[1]), 'kts'],\
               '0-3 km Shear': [fmt(utils.comp2vec(sfc_3km_shear[0], sfc_3km_shear[1])[1]), 'kts'],\
               '0-6 km Shear': [fmt(utils.comp2vec(sfc_6km_shear[0], sfc_6km_shear[1])[1]), 'kts'],\
               '0-8 km Shear': [fmt(utils.comp2vec(sfc_8km_shear[0], sfc_8km_shear[1])[1]), 'kts'],\
               '0-9 km Shear': [fmt(utils.comp2vec(sfc_9km_shear[0], sfc_9km_shear[1])[1]), 'kts']}

    #########################

    # List the indices within the indices dictionary on the side of the plot.
    trans = transforms.blended_transform_factory(ax.transAxes,ax.transData)

    # Write out all of the indices to the figure.
    string = ''
    keys = np.sort(list(indices.keys()))
    x = 0
    counter = 0
    for key in keys:
        string = string + key + ': ' + str(indices[key][0]) + ' ' + indices[key][1] + '\n'
        if counter < 3:
            counter += 1
            continue
        else:
            counter = 0
            ax3.text(x, 1, string, verticalalignment='top', transform=ax3.transAxes, fontsize=11)
            ax3.text(x, 1, string, verticalalignment='top', transform=ax3.transAxes, fontsize=11)
            string = ''
            x += 0.3
    ax3.text(x, 1, string, verticalalignment='top', transform=ax3.transAxes, fontsize=11)
    ax3.set_axis_off()

    #########################

    # Save the figure.
    gs.tight_layout(fig)
    file_out_skewt = file.replace("SPC", "SkewT").strip("txt") + "jpg"  # create output file name
    plt.savefig(os.path.join(directory_out_skewt, file_out_skewt), bbox_inches='tight', dpi=180)
    plt.close(fig)

    # Add lat and lon to indices dictionary.
    indices.update({"Lat": lat, "Lon": lon})

    # Write the indices to a text file.
    file_out_ind = file.replace("SPC", "Indices")  # create output file name
    with open(os.path.join(directory_out_indices, file_out_ind), "w+") as f:            
        f.write(str(indices))
        
    end_time = datetime.now()    
    print("Duration: {}".format(end_time - start_time))

###############################################################################