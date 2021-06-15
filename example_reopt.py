import opentumflex
import os


base_dir = os.path.abspath(os.getcwd())
input_file = r'\input\new1.csv'
output_dir = r'\output'

path_input_data = base_dir + input_file
path_results = base_dir + output_dir

ems,full_ems = opentumflex.run_scenario(opentumflex.scenario_pv,     # Select scenario from scenario.py
                               path_input=path_input_data,              # Input path
                               path_results=path_results,               # Output path
                               solver='glpk',                           # Select solver
                               time_limit=50,                           # Time limit to solve the optimization
                               save_opt_res=False,                      # Save optimization results
                               show_opt_balance=True,                   # Plot energy balance
                               show_opt_soc=True,                      # Plot optimized SOC plan
                               show_flex_res=True,                     # Show flexibility plots
                               show_aggregated_flex=True,               # Plot aggregated flex
                               show_aggregated_flex_price='bar',        # Plot aggregated price as bar/scatter
                               save_flex_offers=False,                  # Save flexibility offers in comax/alf format
                               convert_input_tocsv=False,                # Save .xlsx file to .csv format
                               troubleshooting=False)                   # Troubleshooting on/off
old_ems =ems
while True:
    time_step = int(input("Enter the time step of flexibility:"))
    if time_step == -1:
        break           #for stopping the loop
    type_flex = input("Enter the type of flexibility:")                 #PV_n,PV_p, BAT_p, BAT_n
    
    ems = opentumflex.run_scenario_reopt(opentumflex.scenario_pv,     # Select scenario from scenario.py
                                      old_ems=ems,              # Input path
                                      full_ems = full_ems,
                                      path_results=path_results,               # Output path
                                      reopt_data=[time_step, type_flex],
                                      solver='glpk',                           # Select solver
                                      time_limit=50,                           # Time limit to solve the optimization
                                      save_opt_res=False,                      # Save optimization results
                                      show_opt_balance=True,                   # Plot energy balance
                                      show_opt_soc=True,                      # Plot optimized SOC plan
                                      show_flex_res=True,                     # Show flexibility plots
                                      show_aggregated_flex=True,               # Plot aggregated flex
                                      show_aggregated_flex_price='bar',        # Plot aggregated price as bar/scatter
                                      save_flex_offers=False,                  # Save flexibility offers in comax/alf format
                                      convert_input_tocsv=False,                # Save .xlsx file to .csv format
                                      troubleshooting=False)                   # Troubleshooting on/off
