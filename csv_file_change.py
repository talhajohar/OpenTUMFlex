# -*- coding: utf-8 -*-
"""
Created on Sun May  9 16:30:54 2021

@author: talha
"""

import os
import pandas as pd
import numpy as np

base_dir = os.path.abspath(os.getcwd())
input_file = r'\input\input_newdata.csv'
output_dir = r'C:\Users\talha\OneDrive\Desktop\Tumflex'

path_input_data = base_dir + input_file
path_results = output_dir

data = pd.read_csv(path_input_data,delimiter=';')
data['load_heat'].iloc[25:] = 0

interm = data.iloc[25:].copy()
#interm.reset_index(drop=True)
for b in range(1,3):
    interm['Unnamed: 0'].iloc[0:] = np.arange(0,96) + 96*b
    data = pd.concat([data,interm])

data.to_csv('new1.csv',index = False, sep=';')