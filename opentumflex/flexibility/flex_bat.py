"""
The "flex_pv.py" quantifies the flexibility of battery
"""

__author__ = "Babu Kumaran Nalini"
__copyright__ = "2020 TUM-EWK"
__credits__ = []
__license__ = "GPL v3.0"
__version__ = "1.0"
__maintainer__ = "Babu Kumaran Nalini"
__email__ = "babu.kumaran-nalini@tum.de"
__status__ = "Development"


import pandas as pd
import statistics
import numpy as np


def calc_flex_bat(my_ems, reopt):
    # Find whether optimization or reoptimization
    if reopt == 0:
        dat1 = {'col1': my_ems['optplan']['bat_grid2bat'], 
            'col2': my_ems['optplan']['bat_input_power'],
            'col3': my_ems['optplan']['bat_output_power'],
            'col4': my_ems['optplan']['bat_SOC']}    
    elif reopt == 1:
        dat1 = {'col1': my_ems['reoptim']['optplan']['bat_grid2bat'], 
            'col2': my_ems['reoptim']['optplan']['bat_input_power'],
            'col3': my_ems['reoptim']['optplan']['bat_output_power'],
            'col4': my_ems['reoptim']['optplan']['bat_SOC']}   
    
    dat1 = pd.DataFrame(data=dat1)   
    nsteps = len(dat1)
    ntsteps = my_ems['time_data']['ntsteps']
    Bat_flex = pd.DataFrame(0, index=range(nsteps), columns=range(7))
    Bat_flex.columns = ['Sch_P', 'Neg_P', 'Pos_P', 'Neg_E', 'Pos_E', 'Neg_Pr', 'Pos_Pr']
    
    # Bat_flex.iloc[:, 0] = my_ems['optplan']['bat_grid2bat']
    Bat_maxP = my_ems['devices']['bat']['maxpow']
    Bat_minP = my_ems['devices']['bat']['minpow']
    Bat_maxE = my_ems['devices']['bat']['stocap']
    Bat_minE = 0.500

    # Battery negative flexibility
    for i in range(nsteps):
        Bat_flex.iloc[i, 0] = dat1.iloc[i, 2]  - dat1.iloc[i, 1]
        nflex_P = Bat_maxP-dat1.iloc[i, 1]+dat1.iloc[i, 2]
        if (dat1.iloc[i, 3]*Bat_maxE/100 < Bat_maxE) and (nflex_P > 0):
            #round command changed to np.floor command
            req_steps = int(np.floor(ntsteps*(Bat_maxE-dat1.iloc[i, 3]*Bat_maxE/100)/nflex_P))
            if nflex_P < Bat_minP: #flexibilty power can not be offered as less than minimum power
                req_steps = 0
                
            elif (req_steps != 0) and (req_steps + i <= nsteps-1): 
                req_steps = req_steps + i
            elif req_steps != 0:
                req_steps = nsteps - 1
            #print(i,req_steps,(ntsteps*(Bat_maxE-dat1.iloc[i, 3]*Bat_maxE/100)/nflex_P),nflex_P,dat1.iloc[i, 3])
            if req_steps > 0:                                
                j = i
                while (j < nsteps) and (j < req_steps) and \
                        nflex_P <= (Bat_maxP-dat1.iloc[j, 1]+dat1.iloc[j, 2]): 
                    j = j+1
                Bat_flex.iloc[i, 1] = -1*nflex_P
                Bat_flex.iloc[i, 3] = Bat_flex.iloc[i, 1]*(j-i)/ntsteps
                
            # Usable energy
                cbat_E = 0
                for k in range(j, nsteps):
                    cbat_E = cbat_E + (dat1.iloc[k, 1])/ntsteps  
                
            # Computing the exact flexibility
                neg_Eflex = Bat_flex.iloc[i, 3]
                while (cbat_E < abs(neg_Eflex)) and (j >= i):
                    neg_Eflex = neg_Eflex + abs(Bat_flex.iloc[i, 1]/ntsteps)
    #                cbat_E = cbat_E + (dat1.iloc[j-1, 1]/4)
                    j = j-1
                    Bat_flex.iloc[i, 3] = Bat_flex.iloc[i, 1]*(j-i)/ntsteps
                if j <= i:
                    Bat_flex.iloc[i, 1] = 0
                    Bat_flex.iloc[i, 3] = 0                                     
                    
    # Pricing
    for i in range(nsteps):
        if Bat_flex.iloc[i, 1] < 0 and i < nsteps-1:
            req_steps = int(round(Bat_flex.iloc[i, 3]*ntsteps/Bat_flex.iloc[i, 1]))
            bch_index = [k+i+req_steps for k, l in enumerate(my_ems['optplan']['bat_input_power'][i+req_steps:nsteps]) if l > 0]
            pow_ch = []
            price_ch = []
            for k in range(0, len(bch_index)):
                pow_ch.append(my_ems['optplan']['bat_input_power'][bch_index[k]])
                price_ch.append(my_ems['fcst']['ele_price_in'][bch_index[k]])            
            bat_ch = pd.DataFrame({'slots':bch_index, 'Bat_in':pow_ch, 'price':price_ch})
            bat_ch = bat_ch.sort_values(by=['price'], ascending=False)    
            e_bal = abs(Bat_flex.iloc[i, 3])
            e_prc = 0
            for k in range(0, len(bch_index)):
                if e_bal - bat_ch.iloc[k,1]/ntsteps >= 0:
                    e_bal = e_bal - bat_ch.iloc[k,1]/ntsteps
                    e_prc = e_prc + bat_ch.iloc[k,2]*bat_ch.iloc[k,1]/ntsteps                    
                elif (e_bal - bat_ch.iloc[k,1]/ntsteps < 0) and (e_bal > 0):
                    e_prc = e_prc + bat_ch.iloc[k,2]*e_bal
                    e_bal = 0
            Bat_flex.iloc[i, 5] = e_prc/Bat_flex.iloc[i, 3]
        elif Bat_flex.iloc[i, 1] < 0 and i == nsteps-1:
            Bat_flex.iloc[i, 5] = -1*my_ems['fcst']['ele_price_in'][i]

# PV_Bat_Integration
    # Battery positive flexibility
    # Feeding into the grid
    for i in range(nsteps):
        ava_ebatout = dat1.iloc[i, 3]*Bat_maxE/100 - Bat_minE
        ava_steps = 0
        if ava_ebatout > 0:
            pflex_P = Bat_maxP - dat1.iloc[i, 2]
            #print(pflex_P)
            if pflex_P > 0:
                ava_steps = int(np.floor(ntsteps*ava_ebatout/pflex_P)) #changed round to np.floor
                
                #print(i,ntsteps*ava_ebatout/pflex_P,pflex_P,ava_ebatout)
                if (Bat_maxP - dat1.iloc[i, 2]) < Bat_minP:
                    ava_steps = 0
                elif (ava_steps != 0) and (ava_steps + i <= nsteps-1):
                    ava_steps = ava_steps + i
                elif ava_steps != 0:
                    ava_steps = nsteps-1  
                #print(i,ava_steps)
            if ava_steps > 0:
                j = i
                while (j < nsteps) and (j < ava_steps) and  \
                        pflex_P <= (Bat_maxP - dat1.iloc[j, 2]): #changed formula for flexibility calculation for j time step
                    # Add minimum pos flex power in the previous line
                    j = j+1
                Bat_flex.iloc[i, 2] = pflex_P
                Bat_flex.iloc[i, 4] = Bat_flex.iloc[i, 2]*(j-i)/ntsteps    
                
                # Rechargable energy
                cbat_E = 0
                for k in range(j,nsteps):
                    cbat_E = cbat_E + (Bat_maxP-dat1.iloc[k, 1])/ntsteps       
                
                # Computing the exact flexibility
                pos_Eflex = Bat_flex.iloc[i, 4] 
                while (cbat_E < pos_Eflex) and (j >= i):
                    pos_Eflex = pos_Eflex - Bat_flex.iloc[i, 2]/ntsteps
                    cbat_E = cbat_E + (Bat_maxP-dat1.iloc[j-1, 1])/ntsteps
                    j = j-1
                    Bat_flex.iloc[i, 4] = Bat_flex.iloc[i, 2]*(j-i)/ntsteps
                if j <= i:
                    Bat_flex.iloc[i, 2] = 0
                    Bat_flex.iloc[i, 4] = 0
            
    # Curtailing scheduled charging
    for i in range(nsteps):
         if dat1.iloc[i, 0] > 0:
             j = i
             while (j < nsteps) and (dat1.iloc[i, 0] <= dat1.iloc[j, 0]):
                 j = j+1
             pflex_P = dat1.iloc[i, 1]
             Bat_flex.iloc[i, 2] = Bat_flex.iloc[i, 2] + pflex_P
             Bat_flex.iloc[i, 4] = Bat_flex.iloc[i, 4] + pflex_P*(j-i)/ntsteps  
             
    # Pricing
    for i in range(nsteps):
        if Bat_flex.iloc[i, 2] > 0 and i < nsteps-1:
            min_val = my_ems['fcst']['ele_price_in']
            min_val = statistics.mean(min_val[i:nsteps])
            Bat_flex.iloc[i, 6] = 1*min_val        
        elif Bat_flex.iloc[i, 2] > 0 and i == nsteps-1:
            Bat_flex.iloc[i, 6] = my_ems['fcst']['ele_price_in'][i]
    
    # Insert time column
    # temp = my_ems['time_data']['time_slots'][:]
    # Bat_flex.insert(0,"time",temp)

    my_ems['flexopts']['bat'] = Bat_flex
         
    return my_ems
