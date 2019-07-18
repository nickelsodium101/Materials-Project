# -*- coding: utf-8 -*-
"""
Created on Wed Jul 10 14:10:30 2019

@author: borodnm1
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 10:27:40 2019

@author: borodnm1
"""
import requests
import numpy as np
import os.path
import json
from collections import defaultdict
import re
import pandas as pd
from pandas import DataFrame
import threading, time
from pymongo import MongoClient
import sqlite3

# the stuff that only needs to be run one time

print(time.ctime()) # prints the start time of the code

base_url = 'https://materialsproject.org/rest/v2/'
API_KEY = "sAoUav0smg5jJWDWkbEH"

session = requests.Session()
session.headers.update({'X-API-KEY': API_KEY})

material_data = []

response = session.get(f'https://materialsproject.org/rest/v1/api_check')
data = response.json() # syntax for storing and exchanging data
print(data)

if not data['api_key_valid']:
    raise ValueError('You are not authenticated')

def get_materials(elements):
    '''gets the materials for the elements'''
    elements_str = '-'.join(elements)
    response = session.get(f'{base_url}/materials/{elements_str}/mids')
    data = response.json()
    print(f'Found {len(data["response"])} Materials in the Materials Project with the elements: {elements}')
    return data['response']

def get_material_experimental_properties(mid):
    response = session.get(f'{base_url}/materials/{mid}/exp/')
    print(response.content)
    data = response.json()['response'][0]
    if data == []: # checks to see if data exists
        print("no data exists for that element")
    else:
        print(data)
        return data

def get_material_vasp_properties(mid, piezoelectric = False, dielelectric = False):
    response = session.get(f'{base_url}/materials/{mid}/vasp/')
    material_data = response.json()['response']
    print(response.json()['response'])
    if material_data == []: # checks to see if any data exists for the material data
        print("No data exists for material id: " + str(mid))
    else:
        material_data = response.json()['response'][0]
        
        if piezoelectric: # some important property
            response = session.get(f'{base_url}/materials/{mid}/vasp/piezo')
            data = response.json()
            if not data['valid_response']:
                material_data['piezoelectric'] = None
            else:
                material_data['piezoelectric'] = data['response']
            
        if dielelectric: # another important property
            response = session.get(f'{base_url}/materials/{mid}/vasp/diel')
            data = response.json()
            if not data['valid_response']:
                material_data['dielelectric'] = None
            else:
                material_data['dielelectric'] = data['response']
        
        return material_data

# this is the stuff that needs to be changed each run

def change_materials_pulled(count):
    '''changes the materials pulled by changing the material id
    by 100'''
 
    # generates list of materials needed to pull
    # this list is composed of material ids rather than elements
    # this allows us to iterate through appropriately
    material_list = []
    materials = 'mp-'
    
    total_count = count + 2999
    while count <= total_count: # pulls 3000 materials
        materials = materials + str(count)
        material_list.append(materials)
        materials = 'mp-'
        count += 1
        
    print("Number of materials: " + str(len(material_list)))

    materials_data = {}
    
    for mid in material_list: # for each material in the needed materials
        materials_data[mid] = get_material_vasp_properties(mid) # calculate the properties and add them to the dict
        print("The length of materials data is: " + str(len(materials_data))) # prints len of the dict
    
    print(material_list) # prints out the material list to verify the ids

    # formats the file all nice n pretty
    filename = '{}.json'.format('mp-' + str(count-3000) + '_mp-' + str(total_count)) 
    print(filename)
    try: # checks to see if the file is created
        f = open(filename)                                                                                                                                                               
        f.close()
        
    except FileNotFoundError or IOError: # if the file does not exist, create one
        with open(filename, 'w') as write_file:
            json.dump(materials_data, write_file)

    def convert_dict_to_pandas_frame(data, dict_frames):
        ''' allows the dict to be converted so that we can actually read the data'''
        data_columns = defaultdict(list)
        for d in data.values():
            for key in dict_frames:
                subkey = d
                subkeys = dict_frames[key].split('.')
                for k in subkeys:
                    if re.match(r'\d+', k) and subkey is not None:
                        index = int(k)
                        if index >= len(subkey):
                            subkey = None
                        else:
                            subkey = subkey[index]
                    else:
                        if subkey is not None:
                            subkey = subkey.get(k)
                data_columns[key].append(subkey)
        df = pd.DataFrame.from_dict(data_columns)
        return df.set_index('material_id')
    
    data = json.load(open(filename)) # loads the data
    print('Number of materials: ', len(data))
    
    # views the data
    first_key = next(iter(data))
    data[first_key]
    
    # converts our data to a table
    key_map = {
        'material_id': 'material_id',
        'energy': 'energy',
        'volume': 'volume',
        'nsites': 'nsites',
        'energy_per_atom': 'energy_per_atom',
        'pretty_formula': 'pretty_formula',
        'spacegroup': 'spacegroup.number',
        'band_gap': 'band_gap',
        'density': 'density',
        'total_magnetization': 'total_magnetization',
        # Elacticity
        'poisson_ratio': 'elasticity.poisson_ratio',
        'bulk_modulus_voigt': 'elasticity.K_Voigt',
        'bulk_modulus_reuss': 'elasticity.K_Reuss',
        'bulk_modulus_vrh': 'elasticity.K_VRH',
        'shear_modulus_voigt': 'elasticity.G_Voigt',
        'shear_modulus_vrh': 'elasticity.G_VRH'
    }
    
    df = convert_dict_to_pandas_frame(data, key_map)
    df.info()
    #df.sample(5)
    # write the data to a csv file
    filename = '{}.csv'.format('mp-' + str(count-500) + '_mp-' + str(total_count)) 
    df.to_csv('{}.csv'.format(filename))
    
    # number of materials we're looking at
    len(df)
    
def add_to_mongo_and_sqlite(count):
    '''locates the json file and adds it to the Materials_Project database'''
    
    # adds the data to MongoDB
    client = MongoClient('localhost', 27017)
    db = client['Materials_Project'] # name of database
    
    total_count = count + 499 # for formatting purposes

    filename = '{}.json'.format('mp-' + str(count) + '_mp-' + str(total_count))
    collection_name = '{}'.format('mp-' + str(count) + '_mp-' + str(total_count))
    
    collection = db[collection_name] # creates a collection for the pulled data
    
    with open(filename) as f:
        file_data = json.load(f)

    # adds the json file to the mongo database
    collection.insert_one(file_data)

    client.close() # need to close the database once we're done with it
    #print(client.list_database_names()) 
    print(db.list_collection_names()) # checks to see that the data was added
    
    # adds the data to SQLite
    tablename = '{}'.format('mp-' + str(count) + '_mp-' + str(total_count))

    conn = sqlite3.connect('Materials_Project_Data.db')  # connects to the Materials Project database
    c = conn.cursor() # The database will be saved in the location where your 'py' file is saved
    
    # creates the table name for the file
    c.execute("CREATE TABLE '{table}' (material_id, energy, volume, nsites, energy_per_atom, pretty_formula, spacegroup, band_gap, density,\
                                      total_magnetization, poisson_ratio, bulk_modulus_voigt, bulk_modulus_reuss, bulk_modulus_vrh,\
                                      shear_modulus_voigt, shear_modulus_vrh)".format(table=tablename)) # use your column names here
    conn.commit() # saves this
    
    read_mp = pd.read_csv("/Users/borodnm1/Desktop/'{file}'".format(file=filename)) # access the csv file
    read_mp.to_sql(tablename, conn, if_exists='append', index = False) # Insert the values from the csv file into the created table
    
    conn.commit() # also saves this
    conn.close()

wait_time_seconds = 900 # waits 24 hours

count = 1001 # the count from last time, initalize

# this allows the code to be run every day
ticker = threading.Event()
while not ticker.wait(wait_time_seconds):
    print("starting the program")
    print("Starting with material id: mp-"+ str(count))
    change_materials_pulled(count) # pulls new materials
    add_to_mongo_and_sqlite(count) # adds them to the database
    print("ran the program") 
    count += 3000 # increases the count for the next pull