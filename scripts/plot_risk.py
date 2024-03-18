# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 16:11:12 2024

@author: kingma
"""

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.ticker as mticker

#%% Load the results 
return_periods = ['0p1', '1', '10', '100']
# return_periods = ['1', '10', '100']

risk_folder = Path(r'c:\paramaribo\fiat\4_Results')

# List of scenarios
scenarios = [
            "ref_runx",
            "IG_runx",
            "BAU_runx",
           ]

# List the run labels according to the scenarios above
labels = [
            'Reference',
            'ID 20cm, 7%',
            # 'ID 50cm, 14%',
            # 'BAU current climate',
            'BAU 20cm, 7%',
            # 'BAU 50cm, 14%'
            ]

#%% 
dict_risk = {}
for sc in scenarios:
    if sc[0:3]=='ref':
        risk_path = Path(risk_folder).joinpath(sc).joinpath('current/Risk.txt')
    elif sc[0:3] == 'BAU':
        risk_path = Path(risk_folder).joinpath(sc).joinpath('future_bau/Risk.txt')
    elif sc[0:2] == 'IG':
        risk_path = Path(risk_folder).joinpath(sc).joinpath('future_intgrowth/Risk.txt')
         
    risk = pd.read_csv(risk_path,sep='=',names=['name','risk'])
    risk.set_index('name', inplace=True)  
    risk.index = risk.index.str.replace(' ', '_')
    dict_risk[sc] = pd.DataFrame(risk)

#%% Create subplots
fig, ax = plt.subplots(1, 1, figsize=(10, 6),dpi=500)

# Create lists to store the x and y values for the bar plot
x_values = []
y_values = []

# Iterate over the scenarios and their corresponding risk values
for i, sc in enumerate(scenarios):
    risk_value = dict_risk[sc].loc['Total_damage_risk_', 'risk']
    x_values.append(sc)
    y_values.append(round(risk_value / 1000000, 1))  # Divide by 1,000,000

# Plot the bar chart
bars = ax.bar(x_values, y_values)

# Set the x-axis labels
ax.set_xticks(x_values)
ax.set_xticklabels(labels, rotation=45)  # Set the labels and rotate them if needed

# Add values on top of the bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height, str(height), ha='center', va='bottom')

# Set the y-axis label to display the full risk values in million dollars
ax.set_ylabel('Risk (x 1000000 $)')

# Format the y-axis ticks to display values in million dollars
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f'{x:.1f}'))

ax.set_title('Total EAD [$]')

# Display the plot
plt.show()

#%%
# Create subplots
fig, ax = plt.subplots(1, 1, figsize=(10, 6),dpi=500)

# Create lists to store the x and y values for the bar plot
y_values = []  # Switched from x_values to y_values
x_values = []

# Iterate over the scenarios and their corresponding risk values
for i, sc in enumerate(scenarios):
    risk_value = dict_risk[sc].loc['Total_damage_risk_', 'risk']
    y_values.append(sc)  # Switched from x_values to y_values
    x_values.append(round(risk_value / 1000000, 1))  # Divide by 1,000,000

# Plot the horizontal bar chart
bars = ax.barh(y_values, x_values)  # Use barh to create horizontal bars

# Set the y-axis labels
ax.set_yticks(y_values)  # Switched from set_xticks to set_yticks
ax.set_yticklabels(labels)  # Switched from set_xticklabels to set_yticklabels

# Add values at the end of the bars
for bar in bars:
    width = bar.get_width()  # Switched from height to width
    ax.text(width, bar.get_y() + bar.get_height() / 2, str(width), va='center', ha='left')  # Adjusted text positioning

# Set the x-axis label to display the full risk values in million dollars
ax.set_xlabel('Risk (x 1000000 $)')  # Switched from ax.set_ylabel to ax.set_xlabel

# Format the x-axis ticks to display values in million dollars
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f'{x:.1f}'))

ax.set_title('Total EAD [$]')

# Display the plot
plt.show()


#%%
# Create figure and axes
fig, ax = plt.subplots(1, 1, figsize=(10, 7), dpi=500)

# Colors for the bars
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

# Width of each bar
bar_width = 0.093

# Number of bars to display next to each other
bars_per_xtick = len(scenarios)

# Iterate over scenarios
for i, sc in enumerate(scenarios):
    # Get the risk dataframe for the scenario
    risk_df = dict_risk[sc]
    risk_df = risk_df[:-1]
    risks = risk_df.loc[:, 'risk']
    
    # Get the indexes and risk values
    indexes = risk_df.index
    x_positions = np.arange(len(indexes))

    # Calculate the x positions for the bars within the group
    x = x_positions + i % bars_per_xtick * bar_width * 1.2

    # Plot the bars for the scenario with labels
    ax.bar(x, risks / 1000000, color=colors[i], width=bar_width, label=labels[i])

# Set the x-axis tick positions and labels
ax.set_xticks(x_positions + (bars_per_xtick - 1) * bar_width / 2)
ax.set_xticklabels(indexes, rotation=90)
ax.set_ylabel('Risk (x 1000000 $)')
ax.set_title('Risk per categorie for the different scenarios')
ax.legend()
plt.tight_layout()
plt.show()


#%%
total_per_rp = pd.DataFrame()

for sc in scenarios:
    scenario_data = pd.DataFrame()
    for rp in return_periods:
        if sc[0:3]=='ref':
            risk_path = Path(risk_folder).joinpath(sc).joinpath("current/Flood_rp_" + rp + "/current.txt")
        elif sc[0:3] == 'BAU':
            risk_path = Path(risk_folder).joinpath(sc).joinpath('future_bau/Flood_rp_' + rp + '/future_bau.txt')
        elif sc[0:2] == 'IG':
            risk_path = Path(risk_folder).joinpath(sc).joinpath('future_intgrowth/Flood_rp_' + rp + '/future_intgrowth.txt')
        risk = pd.read_csv(risk_path, sep='|', names=['Category name', 'Damage [USD]', 'Units affected', 'Unit'])
        risk.set_index('Category name', inplace=True)
        scenario_data[rp] = [risk.iloc[-1]['Damage [USD]']]
        scenario_data[rp] = scenario_data[rp].str.replace('.', '').astype(int)

    scenario_data = scenario_data.transpose()
    scenario_data.rename(columns={0: 'damage'}, inplace=True)
    scenario_data['damage'] = scenario_data['damage'] / 1000000
    total_per_rp[sc] = scenario_data['damage']

# Create a subplot with one row and one column
fig, ax = plt.subplots(figsize=(10, 6),dpi=500)

# Plotting the bar plot
width = 0.13
for i, scenario in enumerate(scenarios):
    ax.bar(np.arange(len(total_per_rp.index)) + i * width, total_per_rp[scenario], width=width, label=labels[i])  # Use custom labels

ax.set_xticks(np.arange(len(total_per_rp.index)) + (len(scenarios) - 1) * width / 2)
ax.set_xticklabels(total_per_rp.index)
ax.set_ylabel('Total damage [x1000000 USD]')

for i, scenario in enumerate(scenarios):
    for j, val in enumerate(total_per_rp[scenario]):
        ax.text(j + i * width, val, str(round(val,2)), ha='center', va='top',rotation=90)

ax.set_title('Total risk per return period of the runs')
ax.set_xlabel('Return period')
ax.legend()

plt.show()


#%% Plot the costs per return period 
# Load the results and create the DataFrame for each scenario
# rp = '100'
total_per_rp = {}
num_scenarios = len(scenarios)
num_cols = 2  # Number of columns for subplots
num_rows = (num_scenarios + 1) // num_cols  # Calculate the number of rows needed
fig, axes = plt.subplots(num_rows, num_cols, figsize=(12, 4 * num_rows))

for i,sc in enumerate(scenarios):
    scenario_data = pd.DataFrame()
    for rp in return_periods:
        if sc[0:3]=='ref':
            risk_path = Path(risk_folder).joinpath(sc).joinpath("current/Flood_rp_" + rp + "/current.txt")
        elif sc[0:3] == 'BAU':
            risk_path = Path(risk_folder).joinpath(sc).joinpath('future_bau/Flood_rp_' + rp + '/future_bau.txt')
        elif sc[0:2] == 'IG':
            risk_path = Path(risk_folder).joinpath(sc).joinpath('future_intgrowth/Flood_rp_' + rp + '/future_intgrowth.txt')
        else: print('no categorie')
        risk = pd.read_csv(risk_path, sep='|', names=['Category name', 'Damage [USD]', 'Units affected', 'Unit'])
        risk.set_index('Category name', inplace=True)
        scenario_data[rp] = risk.iloc[6:-2]['Damage [USD]'] 
        scenario_data[rp] = scenario_data[rp].str.replace('.', '').astype(int)
        total_per_rp[sc+"_"+rp] = scenario_data[rp] / 1000000   
    
    scenario_data = total_per_rp[sc+"_"+rp]  # Replace 'sc' with your actual scenario identifier
    row_idx = i // num_cols
    col_idx = i % num_cols
    ax = axes[row_idx, col_idx]  # Get the subplot for this scenario

    # Plot the bar chart for each return period
    scenario_data.plot(kind='barh', ax=ax,label='Return period: '+rp)
    ax.set_title(labels[i]) # Set the scenario name as the subplot title
    ax.set_xlim(0,60)

    # Customize labels, legends, and other plot settings as needed
    ax.set_xlabel(' ')
    ax.set_ylabel(' ')
    ax.legend(loc='upper right')
    ax.grid(linestyle='--', alpha=0.7)
    
    if i >= (len(scenarios)-2):
        ax.set_xlabel('Damage [x1000000 USD]')

# Remove any empty subplots (if the number of scenarios isn't a multiple of 2)
if num_scenarios % 2 != 0:
    empty_ax = axes[-1, -1]
    fig.delaxes(empty_ax)

# Adjust spacing between subplots
plt.tight_layout()

# Show the plot
plt.show()

#%% Plot the risk per categorie per return period 
total_per_rp = {}
num_scenarios = len(scenarios)
num_cols = 2  # Number of columns for subplots
num_rows = (num_scenarios + 1) // num_cols  # Calculate the number of rows needed

for rp in return_periods:
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(12, 4 * num_rows))

    for i,sc in enumerate(scenarios):
        scenario_data = pd.DataFrame()
        if sc[0:3]=='ref':
            risk_path = Path(risk_folder).joinpath(sc).joinpath("current/Flood_rp_" + rp + "/current.txt")
        elif sc[0:3] == 'BAU':
            risk_path = Path(risk_folder).joinpath(sc).joinpath('future_bau/Flood_rp_' + rp + '/future_bau.txt')
        elif sc[0:2] == 'IG':
            risk_path = Path(risk_folder).joinpath(sc).joinpath('future_intgrowth/Flood_rp_' + rp + '/future_intgrowth.txt')
        else: print('no categorie')
        risk = pd.read_csv(risk_path, sep='|', names=['Category name', 'Damage [USD]', 'Units affected', 'Unit'])
        risk.set_index('Category name', inplace=True)
        scenario_data[rp] = risk.iloc[6:-2]['Damage [USD]'] 
        scenario_data[rp] = scenario_data[rp].str.replace('.', '').astype(int)
        total_per_rp[sc+"_"+rp] = scenario_data[rp] / 1000000   
        
        scenario_data = total_per_rp[sc+"_"+rp]  # Replace 'sc' with your actual scenario identifier
        row_idx = i // num_cols
        col_idx = i % num_cols
        ax = axes[row_idx, col_idx]  # Get the subplot for this scenario
    
        # Plot the bar chart for each return period
        scenario_data.plot(kind='barh', ax=ax,label='Return period: '+rp)
        ax.set_title(labels[i]) # Set the scenario name as the subplot title
        ax.set_xlim(0,60)
    
        # Customize labels, legends, and other plot settings as needed
        ax.set_xlabel(' ')
        ax.set_ylabel(' ')
        ax.legend(loc='upper right')
        ax.grid(linestyle='--', alpha=0.7)
        
        # if i >= (len(scenarios)-2):
        #     ax.set_xlabel('Damage [x1000000 USD]')
        ax.set_xlabel('Damage [x1000000 USD]')

    # Remove any empty subplots (if the number of scenarios isn't a multiple of 2)
    if num_scenarios % 2 != 0:
        empty_ax = axes[-1, -1]
        fig.delaxes(empty_ax)
    
    # Adjust spacing between subplots
    plt.tight_layout()
    
    # Show the plot
    plt.show()
    
