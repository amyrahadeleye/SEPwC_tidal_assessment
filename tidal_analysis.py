#!/usr/bin/env python3

# import the modules you need here
import argparse
import pandas as pd
import numpy as np
import uptide
import os
import fnmatch
from scipy.stats import linregress
from matplotlib.dates import date2num


def read_tidal_data(filename):
     # Reads in filename into a pandas dataframe which is cleaned and formatted. Returns the dataframe.
     
     # read in fixed-width file, skipping the header
     df = pd.read_fwf(filename, skiprows=9)
    
     # remove units row
     df.drop(0, inplace=True)
    
     # rename sea level column
     df.rename(columns={df.columns[3]: 'Sea Level'}, inplace=True)
    
     # drop cycle column
     df.drop(columns=df.columns[0], inplace=True)
    
     # remove dodgy values
     df.replace(to_replace=".*T$",value={'Sea Level':np.nan},regex=True,inplace=True)
     df.replace(to_replace=".*N$",value={'Sea Level':np.nan},regex=True,inplace=True)
     df.replace(to_replace=".*M$",value={'Sea Level':np.nan},regex=True,inplace=True)
     df.replace(to_replace=".*T$",value={'Residual':np.nan},regex=True,inplace=True)
     df.replace(to_replace=".*N$",value={'Residual':np.nan},regex=True,inplace=True)
     df.replace(to_replace=".*M$",value={'Residual':np.nan},regex=True,inplace=True)
    
     # convert strings to numbers and datetimes
     df['Date'] = pd.to_datetime(df['Date'], format='%Y/%m/%d')
     df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S') # or pd.to_timedelta(df['Time'], unit='s')
     df['Sea Level'] = df['Sea Level'].astype('float')
     df['Residual'] = df['Residual'].astype('float')
    
     # create datetime column
     df['datetime'] = df['Date'] + pd.to_timedelta(df['Time'].dt.time.astype(str))
    
     # set datetime as index
     df.set_index('datetime', inplace=True)
    
     # NB don't drop Date and Time columns as they are used in tests
     
     return df
    
def extract_section_remove_mean(start, end, data):
   # Takes in dataframe data and returns all rows between start date and end date inclusive.
   # Also removes the mean by normalising the data.

   # Ensure the index is a DatetimeIndex
   if not isinstance(data.index, pd.DatetimeIndex):
      data = data.copy()
      data.index = pd.to_datetime(data.index)
    
   # Convert arguments to datetimes
   start = pd.to_datetime(start).date()
   end = pd.to_datetime(end).date()
    
   # Filter the DataFrame
   data = data[(data.index.date >= start) & (data.index.date <= end)]

   # Normalise sea level to remove the mean as in mini course
   mean_sea_level = np.mean(data['Sea Level'])
   data['Sea Level'] -= mean_sea_level

   return data


def join_data(data1, data2):
   # Joins data1 and data2 vertically and returns the resulting dataframe
   
   # concatenate the data
   combined_data = pd.concat([data1, data2])
   # sort the index by ascending datetime
   combined_data.sort_index(inplace=True)

   return combined_data


def sea_level_rise(data):
   # Uses linear regression to calculate sea level rise in metres per year. Returns the slope (sea level rise) and p value.

   # Remove NaNs
   data = data[~data['Sea Level'].isna()]
   
   # Convert dates to numbers for the regression
   x = date2num(data.index)
   y = data['Sea Level']
   
   # use scipy.stats.linregress
   slope, intercept, r, p, se = linregress(x, y)

   return slope, p

def tidal_analysis(data, constituents, start_datetime):
   # Returns amplitude and phase for given constituents and sea level data using uptide library

   # Need to remove NaNs before calculating tidal constituents
   data = data[~data['Sea Level'].isna()]

   # we create a Tides object with a list of the consituents we want.
   tide = uptide.Tides(constituents)

   # We then set out start time. All data must then be in second since this time
   tide.set_initial_time(start_datetime)

   # calculate seconds since start_datetime
   seconds_since = (data.index.astype('int64').to_numpy()/1e9) - start_datetime.timestamp()

   # Calculate amplitude and phase
   amp, pha = uptide.harmonic_analysis(tide, data['Sea Level'].to_numpy(), seconds_since)
   
   return amp, pha

def get_longest_contiguous_data(data):
    # Returns the start date and end date of the longest contiguous period of data (no missing timestamps or values) as well as the length of this period.

    # Ensure the index is sorted and is a DatetimeIndex
    data = data.sort_index()
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("DataFrame index must be a DatetimeIndex")

    # Step 1: Identify invalid rows (NaN or time gaps)
    valid = data['Sea Level'].notna()
    time_gap = data.index.to_series().diff().gt(pd.Timedelta(hours=1))
    time_gap.iloc[0] = False
    breaks = (~valid) | time_gap

    # Step 2: Mark groups - a new group starts after a break
    group_id = breaks.cumsum()

    # Step 3: Group by group_id and find the longest one
    data_valid = data[~breaks]
    if data_valid.empty:
        return None, None, 0

    groups = data_valid.groupby(group_id)
    longest_group = max(groups, key=lambda g: len(g[1]))

    start = longest_group[1].index[0]
    end = longest_group[1].index[-1]
    length = len(longest_group[1])

    return start, end, length

if __name__ == '__main__':

   parser = argparse.ArgumentParser(
                    prog="UK Tidal analysis",
                    description="Calculate tidal constiuents and RSL from tide gauge data",
                    epilog="Copyright 2024, Jon Hill"
                    )

   parser.add_argument("directory",
                   help="the directory containing txt files with data")
   parser.add_argument('-v', '--verbose',
                   action='store_true',
                   default=False,
                   help="Print progress")

   args = parser.parse_args()
   dirname = args.directory
   verbose = args.verbose

   def load_folder(folder_name):
    # Reads in all .txt files in folder_name and joins them into one text file. This file is returned.

    # Get all txt files in the folder
    txt_files = [f for f in os.listdir(folder_name) if fnmatch.fnmatch(f, '*.txt')]

    data = read_tidal_data(folder_name + '/' + txt_files[0])
    # Concatenate all the txt files into one
    for file in txt_files[1:]:
        data_tmp = read_tidal_data(folder_name + '/' + file)
        data = join_data(data, data_tmp)

    return data
   
   # Load in data
   data = load_folder(dirname)

   # Remove duplicate index values
   data = data[~data.index.duplicated(keep='first')]

   # Calculate longest contiguous period of data
   st, end, length = get_longest_contiguous_data(data)
   print("Start date: ", st, "End date: ", end, "Longest contiguouos period: ", length)

   # Calculate sea-level rise
   slope, p_value = sea_level_rise(data)
   print("Sea level rise rate (slope in metres per unit time): ", slope, "p-value: ", p_value)

   # Calculate tidal data
   constituents  = ['M2', 'S2']
   start_datetime = data.index[0]
   amp, pha = tidal_analysis(data, constituents, start_datetime)
   print("Amplitude of M2, S2: ", amp)
#!/usr/bin/env python3

# import the modules you need here
import argparse

def read_tidal_data(filename):

    return 0
    
def extract_single_year_remove_mean(year, data):
   

    return 


def extract_section_remove_mean(start, end, data):


    return 


def join_data(data1, data2):

    return 



def sea_level_rise(data):

                                                     
    return 

def tidal_analysis(data, constituents, start_datetime):


    return 

def get_longest_contiguous_data(data):


    return 

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
                     prog="UK Tidal analysis",
                     description="Calculate tidal constiuents and RSL from tide gauge data",
                     epilog="Copyright 2024, Jon Hill"
                     )

    parser.add_argument("directory",
                    help="the directory containing txt files with data")
    parser.add_argument('-v', '--verbose',
                    action='store_true',
                    default=False,
                    help="Print progress")

    args = parser.parse_args()
    dirname = args.directory
    verbose = args.verbose
    


