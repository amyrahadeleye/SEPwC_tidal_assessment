#!/usr/bin/env python3

# import the modules you need here
import argparse
import pandas as pd
import numpy as np
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
   df['Sea Level'] = df['Sea Level'].astype('Float')
   df['Residual'] = df['Residual'].astype('Float')
   # create datetime column
   df['datetime'] = df['Date'] + pd.to_timedelta(df['Time'].dt.time.astype(str))

  # set datetime as index
   df.set_index('datetime', inplace=True)

  # NB don't drop Date and Time columns as they are used in tests
   return df
 
    
def extract_single_year_remove_mean(year, data):
# Takes in dataframe data containing multiple years of data and returns a dataframe containing only data from the year year. 
   # Also removes the mean by normalising the data.

   if int(year) in data.index.year:
      data = data[data.index.year == int(year)] # ensure year is an int and not a string
   else:
      print("The data does not contain the given year!")
      return -1

   # Normalise sea level to remove the mean as in mini course
   data['Sea Level'] = data['Sea Level'] - data['Sea Level'].mean()
    
   return data   


  


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
    data['Sea Level'] = data['Sea Level'] - data['Sea Level'].mean()

    return data

    return 


def join_data(data1, data2):
 #Joins data1 and data2 vertically and returns the resulting dataframe
   
   # concatenate the data
   combined_data = pd.concat([data1, data2])
   # sort the index by ascending datetime
   combined_data.sort_index(inplace=True)

   return combined_data




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
    


