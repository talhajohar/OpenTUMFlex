# -*- coding: utf-8 -*-

"""
The "run_scenarios.py" execute all the functional modules within opentumflex folder including initialization,
optimization, flexibility calculation...
"""

__author__ = "Mohammad Talha"

__email__ = "talhajohar@gmail.com"


# new modules
import opentumflex 

# general modules
import os
import numpy as np
import pandas as pd
from copy import deepcopy


    

def run_scenario_reopt(scenario, old_ems,full_ems, path_results,reopt_data=[0 , 'no-flex'], solver='glpk', time_limit=30, troubleshooting=True,
                       show_opt_balance=True, show_opt_soc=True, show_flex_res=True,
                       save_opt_res=True, show_aggregated_flex=True, save_flex_offers=False,
                       convert_input_tocsv=True, show_aggregated_flex_price='bar'):
    """ run an OpenTUMFlex model for given scenario

    Args:
        - scenario: predefined scenario function which will modify the parameters in opentumflex dictionary to create
          a certain scenario
        - path_input: path of input file which can be used to read devices parameters and forecasting data
        - path_results: path to be saved in for results of the optimization
        - fcst_only: if true, read_data() will only read forecasting data from input file, otherwise it will also read
          device parameters
        - time_limit: determine the maximum duration of optimization in seconds

    Returns:
        opentumflex dictionary with optimization results and flexibility offers

    """

    init_time_step = reopt_data[0] #for the ith step find the time
    flex_device = reopt_data[1]  #for the ith step find the device whose offer is to be selected
    full_ems_start_step = 0
    for tim in full_ems['time_data']['time_slots'] == old_ems['time_data']['time_slots'][init_time_step]:
    
        if tim == True:
            break
        else:
            full_ems_start_step += 1

    # initialize with basic time settings
    my_ems = opentumflex.initialize_time_setting(0,t_inval=15, start_time=full_ems['time_data']['time_slots'][full_ems_start_step], end_time=full_ems['time_data']['time_slots'][full_ems_start_step+95])
    if old_ems['reoptim']['flexstep'] == old_ems['time_data']['nsteps']:
        
        my_ems['reoptim']['flexstep'] = init_time_step
       
    else:
        init_time_step = init_time_step - old_ems['reoptim']['flexstep']
        #my_ems = opentumflex.initialize_time_setting(init_time_step,t_inval=15, start_time=old_ems['time_data']['start_time'], end_time='2019-12-18 23:45')

    my_ems['reoptim']['flexstep'] = reopt_data[0]
    


    
    #preparation of my_ems from old_ems
    key_list = list(old_ems['optplan'])
    for ind_para in key_list:
         my_ems['optplan'][ind_para] = full_ems['optplan'][ind_para][full_ems_start_step:full_ems_start_step+96]
         my_ems['optplan'][ind_para][:96-init_time_step] = old_ems['optplan'][ind_para][init_time_step:]
         
    key_list = list(old_ems['flexopts'])
    for ind_para in key_list:
        my_ems['flexopts'][ind_para] = full_ems['flexopts'][ind_para][full_ems_start_step:full_ems_start_step+96]
        my_ems['flexopts'][ind_para].reset_index(drop=True, inplace=True )
    key_list = list(old_ems['fcst'])
    my_ems['fcst'] ={}
    for ind_para in key_list:
        my_ems['fcst'][ind_para] = full_ems['fcst'][ind_para][full_ems_start_step:full_ems_start_step+96]
    my_ems['devices'] = full_ems['devices']
    
    my_ems['reoptim']['type_flex']  = [0] * 96
    
    
    if flex_device == 'PV_n':
        if abs(old_ems['flexopts']['pv']['Neg_P'][init_time_step]) <= 0.000001:
            print('Negative flexibility of PV not available in this time step')
            return old_ems
        inc = 1
        while abs(old_ems['flexopts']['pv']['Neg_P'][init_time_step]) - abs(old_ems['flexopts']['pv']['Neg_P'][init_time_step + inc]) <= 0:
            inc += 1
        
        for a in range(96):
            if a <= inc:
                my_ems['reoptim']['type_flex'][a] = 1
            else:
                
                break
            
        my_ems['reoptim']['flex_value'] = [-1*old_ems['flexopts']['pv']['Neg_P'][init_time_step]] * inc
        my_ems['reoptim']['flex_value'][inc:] = [0] * (96-inc)
          
   
    elif flex_device == 'PV_p':
        if abs(old_ems['flexopts']['pv']['Pos_P'][init_time_step]) <= 0.00001:
            print('Positive flexibility of PV not available in this time step')
            return old_ems
        inc = 1
        while abs(old_ems['flexopts']['pv']['Pos_P'][init_time_step]) <= abs(old_ems['flexopts']['pv']['Pos_P'][init_time_step + inc]):
            inc += 1
        for a in range(96):
            
            if a <= inc:
                my_ems['reoptim']['type_flex'][a] = 2
            else:
                
                break
            
        my_ems['reoptim']['flex_value'] = [old_ems['flexopts']['pv']['Pos_P'][init_time_step]] * inc
        my_ems['reoptim']['flex_value'][inc:] = [0] * (96-inc)
    
    elif flex_device == 'BAT_n':
        
        if abs(old_ems['flexopts']['bat']['Neg_P'][init_time_step]) <= 0.000001:
            print('Negative flexibility of Battery not available in this time step')
            return old_ems
        inc = 0
        bat_SOC = old_ems['optplan']['bat_SOC'][init_time_step-1]
        ntsteps = old_ems['time_data']['ntsteps']
        stocap = old_ems['devices']['bat']['stocap']
        max_pow = old_ems['devices']['bat']['maxpow']
       
        
        while bat_SOC + max_pow/ (ntsteps*stocap)*100 <= 100 :
            inc += 1
            bat_SOC +=  max_pow/ (ntsteps*stocap)*100
            
        for a in range(96):
            
            if a < inc:
                my_ems['reoptim']['type_flex'][a] = 3
            else:
                
                break
            
        my_ems['reoptim']['flex_value'] = [-1*old_ems['flexopts']['bat']['Neg_P'][init_time_step]] * inc
        my_ems['reoptim']['flex_value'][inc:] = [0] * (96-inc)
    
    
    elif flex_device == 'BAT_p':
        if abs(old_ems['flexopts']['bat']['Pos_P'][init_time_step]) <= 0.000001:
            print('Positive flexibility of Battery not available in this time step')
            return old_ems
        inc = 0
        bat_SOC = old_ems['optplan']['bat_SOC'][init_time_step-1]
        ntsteps = old_ems['time_data']['ntsteps']
        stocap = old_ems['devices']['bat']['stocap']
        max_pow = old_ems['devices']['bat']['maxpow']
        
        while bat_SOC - max_pow/ (ntsteps*stocap)*100 >= 0 :
            inc += 1
            bat_SOC -=  max_pow/ (ntsteps*stocap)*100
            
        for a in range(96):
            
            if a < inc:
                my_ems['reoptim']['type_flex'][a] = 4
            else:
                
                break
            
        my_ems['reoptim']['flex_value'] = [old_ems['flexopts']['bat']['Pos_P'][init_time_step]] * inc
        
        my_ems['reoptim']['flex_value'][inc:] = [0] * (96-inc)
        
     
    
    #storing flexibilty value for further calculations in the code
    flex_value = deepcopy(my_ems['reoptim']['flex_value'][0])
    
    #setting up SOC of my_ems equal to the last step before implementation of reoptimizaiton
    my_ems['devices']['bat']['initSOC'] = old_ems['optplan']['bat_SOC'][init_time_step-1]
    
    #creating deepcopy so that changes in my_ems_without_flex does not bring changes in my_ems
    my_ems_without_flex = deepcopy(my_ems)
    #setting type flexibility to 0 in order to run the original model wihtout flexibility constrainst
    for a in range(96):
        my_ems_without_flex['reoptim']['type_flex'][a] = 0
    
    my_ems_without_flex['reoptim']['flex_value'] = [0] * 96
    
 
    #forming ems without flexibility offer for comparison  
    
    m_without_flex = opentumflex.create_model(my_ems_without_flex)

    m_without_flex = opentumflex.solve_model(m_without_flex, solver=solver, time_limit=time_limit, troubleshooting=troubleshooting)

    my_ems_without_flex = opentumflex.extract_res(m_without_flex, my_ems_without_flex)
    


    
    #solving mes with flexibility offer  
    m = opentumflex.create_model(my_ems)

    m = opentumflex.solve_model(m, solver=solver, time_limit=time_limit, troubleshooting=troubleshooting)

    my_ems = opentumflex.extract_res(m, my_ems)
    
    calc_flex = {opentumflex.calc_flex_hp: 'hp',
                opentumflex.calc_flex_ev: 'ev',
                opentumflex.calc_flex_chp: 'chp',
                opentumflex.calc_flex_bat: 'bat',
                opentumflex.calc_flex_pv: 'pv'}
    
   
   

    
        

    # visualize the optimization results
    opentumflex.plot_optimal_results(my_ems, show_balance=show_opt_balance, show_soc=show_opt_soc)
    
    #the one below compares result of reoptimization starting from the instance of offer selection
    #opentumflex.compare_optimal_results(my_ems, my_ems_without_flex,0,inc)
    
    #the code below compares optimization result starting from the start point of old_ems
    historical_data = True
    if historical_data == True:
        my_ems_without_flex_hd = {}
        my_ems_without_flex_hd['devices'] = old_ems['devices']
        my_ems_without_flex_hd['fcst'] = old_ems['fcst']
        my_ems_without_flex_hd['time_data'] = old_ems['time_data']
        my_ems_without_flex_hd['optplan'] =  old_ems['optplan']
        my_ems_without_flex_hd['flexopts']  = old_ems['flexopts']
        my_ems_hd = deepcopy(my_ems_without_flex_hd)
        my_ems_hd['reoptim'] ={} 
        my_ems_hd['reoptim']['flex_value'] = [0]*len(my_ems['time_data']['time_slots'])
        my_ems_hd['reoptim']['flex_value'][init_time_step:init_time_step+inc] = [my_ems['reoptim']['flex_value'][0]] * inc 
        
        
        key_list = list(old_ems['optplan'])
        
        for ind_para in key_list:
             my_ems_without_flex_hd['optplan'][ind_para][init_time_step:] =  my_ems_without_flex['optplan'][ind_para][:96-init_time_step]
             my_ems_hd['optplan'][ind_para][init_time_step:] =  my_ems['optplan'][ind_para][:96-init_time_step]
        
        
        
        key_list = list(old_ems['flexopts'])
        for ind_para in key_list:
             my_ems_without_flex_hd['flexopts'][ind_para][init_time_step:] =  np.array(my_ems_without_flex['flexopts'][ind_para][:96-init_time_step])
             my_ems_hd['flexopts'][ind_para][init_time_step:] =  np.array(my_ems['flexopts'][ind_para][:96-init_time_step])
        
        opentumflex.compare_optimal_results(my_ems_hd, my_ems_without_flex_hd,init_time_step,init_time_step+inc,flex_device,flex_value)
    
    
    
    
    
    #the code below makes the calculation for two cases: 1)revenue generation without flexibity 2) revenue generation with flexibility
    ntsteps = old_ems['time_data']['ntsteps']
    
    Revenue_without_flex = np.empty(((len(my_ems_without_flex['time_data']['time_slots'])+1,2)))
    #Revenue_without_flex['Time_slots']= np.array(my_ems_without_flex['time_data']['time_slots'])
    Revenue_without_flex[:-1,0] = np.array(my_ems_without_flex['fcst']['ele_price_out']) *  np.array(my_ems_without_flex['optplan']['grid_export'])/ntsteps
    Revenue_without_flex[:-1,1] = np.array(my_ems_without_flex['fcst']['ele_price_in']) *  np.array(my_ems_without_flex['optplan']['grid_import'])/ntsteps
    
    Revenue_without_flex[-1,0] = np.sum(Revenue_without_flex[:-1,0])
    Revenue_without_flex[-1,1] = np.sum(Revenue_without_flex[:-1,1])
    
    Revenue_with_flex = np.empty(((len(my_ems_hd['time_data']['time_slots'])+1,3)))
    #Revenue_with_flex['Time_slots']= np.array(my_ems_hd['time_data']['time_slots'])
    Revenue_with_flex[:-1,0] = np.array(my_ems_hd['fcst']['ele_price_out']) *  np.array(my_ems_hd['optplan']['grid_export'])/ntsteps
    Revenue_with_flex[:-1,1] = np.array(my_ems_hd['fcst']['ele_price_in']) *  np.array(my_ems_hd['optplan']['grid_import'])/ntsteps
    if flex_device == 'PV_p':
        Revenue_with_flex[:-1,2] = np.array(my_ems_hd['flexopts']['pv']['Pos_Pr'][init_time_step]) *  np.array(my_ems_hd['reoptim']['flex_value']) /ntsteps
    elif flex_device == 'PV_n':
        Revenue_with_flex[:-1,2] = np.array(my_ems_hd['flexopts']['pv']['Neg_Pr'][init_time_step]) *  np.array(my_ems_hd['reoptim']['flex_value']) /ntsteps
    elif flex_device == 'BAT_p':
        Revenue_with_flex[:-1,2] = np.array(my_ems_hd['flexopts']['bat']['Pos_Pr'][init_time_step]) *  np.array(my_ems_hd['reoptim']['flex_value']) /ntsteps
    elif flex_device == 'BAT_n':
        Revenue_with_flex[:-1,2] = np.array(my_ems_hd['flexopts']['bat']['Neg_Pr'][init_time_step]) *  np.array(my_ems_hd['reoptim']['flex_value']) /ntsteps

    
    
    Revenue_with_flex[-1,0] = np.sum(Revenue_with_flex[:-1,0])
    Revenue_with_flex[-1,1] = np.sum(Revenue_with_flex[:-1,1])
    Revenue_with_flex[-1,2] = np.sum(Revenue_with_flex[:-1,2])
    
    index = my_ems_without_flex['time_data']['time_slots']
    index = index.append(pd.Index(['Total']))
    columns_withouttf = ['Export Earning','Import Expenditure']
    columns_withtf = ['Export Earning','Import Expenditure','Flexibility Earning']
    Revenue_withoutf = pd.DataFrame(Revenue_without_flex,index = index,columns =columns_withouttf)
    Revenue_withf = pd.DataFrame(Revenue_with_flex,index = index,columns =columns_withtf)
    
    
    revenue_minus_expenditure_withf = Revenue_with_flex[-1,0] - Revenue_with_flex[-1,1] + Revenue_with_flex[-1,2]  
    revenue_minus_expenditure_withoutf = Revenue_without_flex[-1,0]- Revenue_without_flex[-1,1]
    
    Net_gain = revenue_minus_expenditure_withf -  revenue_minus_expenditure_withoutf
    print(Net_gain)
    
    
    
    
    
    
    # save the data in .xlsx in given path
    if save_opt_res:
        opentumflex.save_results(my_ems, path_results)
        

    
    # plot the results of flexibility calculation
    if show_flex_res:
        for device_name in calc_flex.values():
            if my_ems['devices'][device_name]['maxpow'] != 0:
                opentumflex.plot_flex(my_ems, device_name)
                
    # plot stacked flexibility of all devices
    if show_aggregated_flex:
        opentumflex.plot_aggregated_flex_power(my_ems)
        opentumflex.plot_aggregated_flex_price(my_ems, plot_flexpr=show_aggregated_flex_price)    

    # save flex offers
    if save_flex_offers:
        opentumflex.save_offers(my_ems, market='comax')
    
    
 
    
    
    return my_ems

if __name__ == '__main__':
    base_dir = os.path.abspath(os.getcwd())
    input_file = r'\..\input\input_data.csv'
    output_dir = r'\..\results'
    path_input_data = base_dir + input_file
    path_results = base_dir + output_dir

    # ems = run_scenario(opentumflex.scenario_apartment,
    #                    path_input=path_input_data, path_results=path_results,
    #                    fcst_only=True, time_limit=10,
    #                    show_flex_res=True, show_opt_res=True, save_opt_res=False,
    #                    convert_input_tocsv=True, show_aggregated_flex=True, 
    #                    show_aggregated_flex_price='bar', troubleshooting=False)

