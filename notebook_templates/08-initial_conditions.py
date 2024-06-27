# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: subspace
#     language: python
#     name: subspace
# ---

# %% [markdown] papermill={"duration": 0.004527, "end_time": "2024-01-31T00:37:20.089887", "exception": false, "start_time": "2024-01-31T00:37:20.085360", "status": "completed"}
# # Subspace Digital Twin, Initial Conditions Run
#
# *Shawn Anderson, January 2024*
#
# In this notebook, we examine medianl behavior over the first 90 days.

# %% [markdown] papermill={"duration": 0.003163, "end_time": "2024-01-31T00:37:20.100107", "exception": false, "start_time": "2024-01-31T00:37:20.096944", "status": "completed"}
# ## Part 1. Dependences & Set-up

# %% [markdown] papermill={"duration": 0.003026, "end_time": "2024-01-31T00:37:20.106235", "exception": false, "start_time": "2024-01-31T00:37:20.103209", "status": "completed"}
# Autoreload modules while developing.

# %% papermill={"duration": 1.253531, "end_time": "2024-01-31T00:37:21.362869", "exception": false, "start_time": "2024-01-31T00:37:20.109338", "status": "completed"}
# %load_ext autoreload
# %autoreload 2

import sys
sys.path.append('../')

import numpy as np
import pandas as pd
pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

import hvplot.pandas
hvplot.extension('bokeh')

from bokeh.models import HoverTool
import holoviews as hv

from bokeh.palettes import Turbo256, Category20

# %% [markdown] papermill={"duration": 0.007853, "end_time": "2024-01-31T00:37:21.375298", "exception": false, "start_time": "2024-01-31T00:37:21.367445", "status": "completed"}
# ## Part 2. Load Simulation Data

# %% [markdown] papermill={"duration": 0.004393, "end_time": "2024-01-31T00:37:21.387874", "exception": false, "start_time": "2024-01-31T00:37:21.383481", "status": "completed"}
# Load the simulation results data.

# %% papermill={"duration": 0.019539, "end_time": "2024-01-31T00:37:21.430033", "exception": false, "start_time": "2024-01-31T00:37:21.410494", "status": "completed"}
sim_df = pd.read_pickle(
    "../../data/simulations/initial_conditions-2024-06-24_22-33-45.pkl.gz"
).drop(['timestep', 'simulation', 'subset', 'timestep_in_days', 'block_time_in_seconds', 'delta_days', 'delta_blocks'], axis=1)

# %% papermill={"duration": 0.026983, "end_time": "2024-01-31T00:37:21.461524", "exception": false, "start_time": "2024-01-31T00:37:21.434541", "status": "completed"}
sim_df.head(5)

# %% [markdown] papermill={"duration": 0.004374, "end_time": "2024-01-31T00:37:21.470285", "exception": false, "start_time": "2024-01-31T00:37:21.465911", "status": "completed"}
# Simulation Runs.

# %% papermill={"duration": 0.016922, "end_time": "2024-01-31T00:37:21.491475", "exception": false, "start_time": "2024-01-31T00:37:21.474553", "status": "completed"}
sim_df.groupby(['run', 'label', 'environmental_label']).size().reset_index(name='Days').head()

# %% [markdown] papermill={"duration": 0.004318, "end_time": "2024-01-31T00:37:21.500198", "exception": false, "start_time": "2024-01-31T00:37:21.495880", "status": "completed"}
# ### Coloring Metrics
# Use a constant mapping from columns to colors

# %% papermill={"duration": 0.124504, "end_time": "2024-01-31T00:37:21.628948", "exception": false, "start_time": "2024-01-31T00:37:21.504444", "status": "completed"}
color_palette = Category20
# columns_to_color = sorted(list(set(sim_df.columns) - {'environmental_label', 'label', 'run', 'blocks_passed', 'days_passed'}))
columns_to_color = sim_df.columns
if color_palette == Turbo256:
    column_colors = dict(zip(columns_to_color, [color_palette[int(i)] for i in np.linspace(0,len(color_palette)-1, len(columns_to_color))]))

if color_palette == Category20:
    column_colors = {col: Category20[20][i%20] for i, col in enumerate(columns_to_color)}


sim_df.count().to_frame().T.hvplot.bar(y=columns_to_color, color=[column_colors[c] for c in columns_to_color], rot=90, width=1400, height=500, title='Column Color Map', fontscale=1.4, yaxis=None)


# %% papermill={"duration": 0.021418, "end_time": "2024-01-31T00:37:21.655322", "exception": false, "start_time": "2024-01-31T00:37:21.633904", "status": "completed"}
def snake_to_title(s):
    """Utility function used for printing chart titles and labels as Title Case.
    Example:
    snake_to_caps('snake_case')
    >>> 'Snake Case'
    """
    
    return ' '.join(word.capitalize() for word in s.split('_'))

def fan_chart_quantile_median(df, column='circulating_supply', median_only=False):
    """Combine an area chart of min-max and a line chart of median for a series."""

    # min, max, median
    fan_df = df.groupby('days_passed')[column].agg(['min', 'max', 'median'])

    opts = dict(width=1200, height=500, title=f'{snake_to_title(column)} Fan Chart', ylabel=f'{column}_min_max_median')

    # Median curve
    hover = HoverTool(tooltips=[(f'{snake_to_title(column)} Median', '@median{0,0.00}')])
    median_chart = fan_df.hvplot(x='days_passed', y='median', alpha=1, line_width=4, label=f'{snake_to_title(column)} Median', tools=[hover], color=column_colors[column]).opts(**opts)
    if median_only:
        return median_chart

    # min-max band
    hover = HoverTool(tooltips=[(f'{snake_to_title(column)} Days Passed', '$x{0,0}')])
    bands_chart = fan_df.hvplot.area(x='days_passed', y='min', y2='max', legend='top_left', alpha=0.4, tools=[hover], ylim=(0,None), color=column_colors[column]).opts(**opts)

    # Composition
    chart = bands_chart * median_chart
    return chart


def fan_chart_quantile(df, column='circulating_supply', median_only=False):
    """Combine an area chart of min-max and a line chart of quantile for a series."""

    # 25%, 50%, 75%
    fan_df = df.groupby('days_passed')[column].quantile([0.25, 0.5, 0.75]).unstack().rename(columns={0.50:'median', 0.25:'0.25',0.75:'0.75'})

    # return fan_df

    opts = dict(width=1200, height=500, title=f'{snake_to_title(column)} Quantile Fan Chart', ylabel=f'{column}_quantile')

    # Quantile curve
    hover = HoverTool(tooltips=[(f'{snake_to_title(column)} Median', '@median{0,0.00}')])
    quatile_chart = fan_df.hvplot(x='days_passed', y='median', alpha=1, line_width=4, label=f'{snake_to_title(column)} Quantile', tools=[hover], color=column_colors[column]).opts(**opts)
    if median_only:
        return quatile_chart

    # min-max band
    hover = HoverTool(tooltips=[(f'{snake_to_title(column)} Days Passed', '$x{0,0}')])
    bands_chart = fan_df.hvplot.area(x='days_passed', y='0.25', y2='0.75', legend='top_left', alpha=0.4, tools=[hover], ylim=(0,None), color=column_colors[column]).opts(**opts)

    # Composition
    chart = bands_chart * quatile_chart
    return chart



# %% papermill={"duration": 0.088119, "end_time": "2024-01-31T00:37:21.747980", "exception": false, "start_time": "2024-01-31T00:37:21.659861", "status": "completed"}
fan_chart_quantile_median(sim_df, column='circulating_supply', median_only=False)

# %% papermill={"duration": 0.08539, "end_time": "2024-01-31T00:37:21.838219", "exception": false, "start_time": "2024-01-31T00:37:21.752829", "status": "completed"}
fan_chart_quantile(sim_df, column='circulating_supply', median_only=False)

# %% [markdown] papermill={"duration": 0.004888, "end_time": "2024-01-31T00:37:21.848374", "exception": false, "start_time": "2024-01-31T00:37:21.843486", "status": "completed"}
# ### Stocks
#
# The listed stocks are of four types, which are 
# 1) **Agent Treasuries**, that consists of a) Farmers Balance, b) Operators Balance, c) Users Balance and d) Nominators Balance; 
# 2) **Agent Pools**, of which there is an single one: the Operator Staking Pool; 
# 3) **Protocol Treasuries**, which consists of a) Designated Storage Fund and b) Escrow Fund.
# 4) **Other**, of which there is an single one: Protocol Issuance.
#
# From an aggregated sectorial perspective, the full description of the token dynamics is done by writing the initial state of the stocks and to formally define the flows between them. One **assumption** is as follows:
#
#
# | Stock | Type | SSC Quantity at time zero | 
# | - | - | - | 
# | Protocol Issuance | Other | $\text{TotalIssuance} - \sum \text{Stocks}(t=0)$ | 
# |Escrow Fund | Protocol Treasuries | 0.0 |
# |Designated Storage Fund | Protocol Treasuries | 0.0 |
# |Farmers Balance | Agent Treasuries | 0.0 |
# |Operators Balance | Agent Treasuries | 0.0 |
# |Nominators Balance | Agent Treasuries | 0.0 |
# |Users Balance | Agent Treasuries | $10\%$ of $\text{TotalIssuance}$ |
# |Operator Staking Pool | Agent Pools | 0.0 |
#
# Source:  
# https://hackmd.io/ywJv4YxfQla3DOktqA9zdg?view#Stocks  
# Authors:  
# Danilo Lessa Bernardineli (BlockScience), September 2023

# %% [markdown] papermill={"duration": 0.004749, "end_time": "2024-01-31T00:37:21.858166", "exception": false, "start_time": "2024-01-31T00:37:21.853417", "status": "completed"}
# ## SSC Balances Over Time

# %% [markdown] papermill={"duration": 0.004785, "end_time": "2024-01-31T00:37:21.867820", "exception": false, "start_time": "2024-01-31T00:37:21.863035", "status": "completed"}
# System Balances

# %% papermill={"duration": 0.014674, "end_time": "2024-01-31T00:37:21.887251", "exception": false, "start_time": "2024-01-31T00:37:21.872577", "status": "completed"}
system_balances = ['vesting_balance', 'reward_issuance_balance']

# %% papermill={"duration": 0.275799, "end_time": "2024-01-31T00:37:22.168260", "exception": false, "start_time": "2024-01-31T00:37:21.892461", "status": "completed"}
hover = HoverTool(
    tooltips=[('Days Passed', '$x{0,0}')]
)
colors = [column_colors[c] for c in system_balances]
sim_df.hvplot.area(x='days_passed', y=system_balances, groupby='run', stacked=True, alpha=1, width=1200, height=500, legend='top_right', ylabel='SSC', tools=[hover], ylim=(0,None), title='SSC System Daily Balances Stacked by Run', color=colors)

# %% papermill={"duration": 0.130072, "end_time": "2024-01-31T00:37:22.303766", "exception": false, "start_time": "2024-01-31T00:37:22.173694", "status": "completed"}
hv.Overlay([fan_chart_quantile(sim_df, c) for c in system_balances]).opts(title='SSC System Daily Balances Fan Chart Comparison', ylabel='SSC')

# %% [markdown] papermill={"duration": 0.008613, "end_time": "2024-01-31T00:37:22.318075", "exception": false, "start_time": "2024-01-31T00:37:22.309462", "status": "completed"}
# ### Weekly Aggregation

# %% papermill={"duration": 0.024145, "end_time": "2024-01-31T00:37:22.347708", "exception": false, "start_time": "2024-01-31T00:37:22.323563", "status": "completed"}
# Create a weekly index
sim_df['weeks_passed'] = sim_df['days_passed'] // 7

# Group by the weekly index and aggregate, then filter out incomplete weeks
weekly_aggregated_df = (
    sim_df.groupby(['run', 'weeks_passed'])
    .filter(lambda x: len(x) == 7)  # Assuming each week should have 7 days
    .groupby(['run', 'weeks_passed'])
    .sum()
)

# %% papermill={"duration": 0.124441, "end_time": "2024-01-31T00:37:22.477761", "exception": false, "start_time": "2024-01-31T00:37:22.353320", "status": "completed"}
weekly_aggregated_df.hvplot.bar(x='weeks_passed', y=system_balances, groupby='run', stacked=False, alpha=1, width=1200, height=500, legend='top_right', ylabel='SSC', tools=[hover], ylim=(0,None), title='SSC System Weekly Balances Compared by Run', rot=90, color=colors).opts(multi_level=False)

# %% [markdown] papermill={"duration": 0.008528, "end_time": "2024-01-31T00:37:22.492415", "exception": false, "start_time": "2024-01-31T00:37:22.483887", "status": "completed"}
# ### Agent Treasuries
# Consists of a) Farmers Balance, b) Operators Balance, c) Users Balance and d) Nominators Balance

# %% papermill={"duration": 0.015785, "end_time": "2024-01-31T00:37:22.513937", "exception": false, "start_time": "2024-01-31T00:37:22.498152", "status": "completed"}
agent_balances = [
    'farmers_balance',
    'operators_balance',
    'user_supply',
    'nominators_balance',
]

# %% papermill={"duration": 0.16151, "end_time": "2024-01-31T00:37:22.681359", "exception": false, "start_time": "2024-01-31T00:37:22.519849", "status": "completed"}
weekly_aggregated_df.hvplot.area(x='weeks_passed', y=agent_balances, groupby='run', stacked=True, alpha=0.9, width=1200, height=500, legend='top_left', ylabel='SSC', tools=[hover], ylim=(0,None), title='SSC Agent Weekly Balances Stacked by Run', color=[column_colors[c] for c in agent_balances])

# %% papermill={"duration": 0.205887, "end_time": "2024-01-31T00:37:22.893502", "exception": false, "start_time": "2024-01-31T00:37:22.687615", "status": "completed"}
hv.Overlay([fan_chart_quantile(weekly_aggregated_df, c) for c in agent_balances]).opts(title='SSC Agent Weekly Balances Fan Chart Comparison', ylabel='SSC', legend_opts={'location':'top_left'})

# %% [markdown] papermill={"duration": 0.008202, "end_time": "2024-01-31T00:37:22.908258", "exception": false, "start_time": "2024-01-31T00:37:22.900056", "status": "completed"}
# ### Agent Pools
# There is an single one: the Operator Staking Pool

# %% papermill={"duration": 0.090059, "end_time": "2024-01-31T00:37:23.004450", "exception": false, "start_time": "2024-01-31T00:37:22.914391", "status": "completed"}
agent_pool_balances = ['staking_pool_balance']

hv.Overlay([fan_chart_quantile(weekly_aggregated_df, c) for c in agent_pool_balances]).opts(title='SSC Agent Pools Weekly Balances', ylabel='SSC', legend_opts={'location':'top_left'})

# %% [markdown] papermill={"duration": 0.008058, "end_time": "2024-01-31T00:37:23.020269", "exception": false, "start_time": "2024-01-31T00:37:23.012211", "status": "completed"}
# ### Protocol Treasuries
# Consists of a) Designated Storage Fund and b) Escrow Fund.

# %% papermill={"duration": 0.092071, "end_time": "2024-01-31T00:37:23.118618", "exception": false, "start_time": "2024-01-31T00:37:23.026547", "status": "completed"}
protocol_treasury_balances = ['fund_balance']

hv.Overlay([fan_chart_quantile(weekly_aggregated_df, c) for c in protocol_treasury_balances]).opts(title='SSC Agent Pools Weekly Balances', ylabel='SSC', legend_opts={'location':'top_left'})

# %% [markdown] papermill={"duration": 0.006438, "end_time": "2024-01-31T00:37:23.131842", "exception": false, "start_time": "2024-01-31T00:37:23.125404", "status": "completed"}
# ### Other Balances

# %% papermill={"duration": 0.01803, "end_time": "2024-01-31T00:37:23.156293", "exception": false, "start_time": "2024-01-31T00:37:23.138263", "status": "completed"}
other_balances = list(set([c for c in sim_df.columns if 'balance' in c]) - set(system_balances + agent_balances + agent_pool_balances + protocol_treasury_balances) )
other_balances

# %% papermill={"duration": 0.133836, "end_time": "2024-01-31T00:37:23.296604", "exception": false, "start_time": "2024-01-31T00:37:23.162768", "status": "completed"}
weekly_aggregated_df.hvplot.area(x='weeks_passed', y=other_balances, groupby='run', stacked=True, alpha=0.9, width=1200, height=500, legend='top_left', ylabel='SSC', tools=[hover], ylim=(0,None), title='SSC Agent Weekly Balances Stacked', color=[column_colors[c] for c in other_balances])

# %% papermill={"duration": 0.1286, "end_time": "2024-01-31T00:37:23.433354", "exception": false, "start_time": "2024-01-31T00:37:23.304754", "status": "completed"}
hv.Overlay([fan_chart_quantile(weekly_aggregated_df, c) for c in other_balances]).opts(title='SSC Other Weekly Balances', ylabel='SSC', legend_opts={'location':'top_left'})

# %% [markdown] papermill={"duration": 0.008143, "end_time": "2024-01-31T00:37:23.448596", "exception": false, "start_time": "2024-01-31T00:37:23.440453", "status": "completed"}
# ## SSC Supply Over Time

# %% papermill={"duration": 0.018085, "end_time": "2024-01-31T00:37:23.473658", "exception": false, "start_time": "2024-01-31T00:37:23.455573", "status": "completed"}
supply_columns = list({c for c in sim_df.columns if 'supply' in c} - {'max_credit_supply', 'issued_supply', 'total_supply'})
supply_columns

# %% papermill={"duration": 0.21432, "end_time": "2024-01-31T00:37:23.694957", "exception": false, "start_time": "2024-01-31T00:37:23.480637", "status": "completed"}
hv.Overlay([fan_chart_quantile(weekly_aggregated_df, c) for c in supply_columns]).opts(title='SSC Other Weekly Balances', ylabel='SSC', legend_opts={'location':'top_left'})

# %% papermill={"duration": 0.240145, "end_time": "2024-01-31T00:37:23.942819", "exception": false, "start_time": "2024-01-31T00:37:23.702674", "status": "completed"}
sim_df.hvplot.area(x='days_passed', y=supply_columns, groupby='run', stacked=True, alpha=0.9, width=1200, height=500, legend='top_right', ylabel='SSC', tools=[hover], ylim=(0,None))

# %% papermill={"duration": 0.169468, "end_time": "2024-01-31T00:37:24.120050", "exception": false, "start_time": "2024-01-31T00:37:23.950582", "status": "completed"}
hv.Overlay([fan_chart_quantile(weekly_aggregated_df, c) for c in ['max_credit_supply', 'issued_supply', 'total_supply']]).opts(title='SSC Other Weekly Balances', ylabel='SSC', legend_opts={'location':'bottom_right'})

# %% [markdown] papermill={"duration": 0.008849, "end_time": "2024-01-31T00:37:24.137040", "exception": false, "start_time": "2024-01-31T00:37:24.128191", "status": "completed"}
# ### Explore Normalized Numeric Simulation Results

# %% papermill={"duration": 0.022267, "end_time": "2024-01-31T00:37:24.166672", "exception": false, "start_time": "2024-01-31T00:37:24.144405", "status": "completed"}
df = weekly_aggregated_df#.set_index('weeks_passed')

# Take numeric columns for normalizationn
df_numeric = df.select_dtypes(include=['number'])

# Create the normalized results
df_normalized = df_numeric / df_numeric.max()

# Add the label column back
df_normalized[['label', 'environmental_label']] = df[['label', 'environmental_label']]

# Drop unecessary columns
df_normalized = df_normalized.drop(['label', 'environmental_label', 'sum_of_stocks', 'buffer_size'], axis=1).fillna(0)
df_normalized.shape

# %% papermill={"duration": 0.046902, "end_time": "2024-01-31T00:37:24.223190", "exception": false, "start_time": "2024-01-31T00:37:24.176288", "status": "completed"}
df_normalized.describe()

# %% [markdown] papermill={"duration": 0.009562, "end_time": "2024-01-31T00:37:24.240814", "exception": false, "start_time": "2024-01-31T00:37:24.231252", "status": "completed"}
# ### Normalized Weekly Means of All Numeric Columns

# %% papermill={"duration": 0.772381, "end_time": "2024-01-31T00:37:25.020862", "exception": false, "start_time": "2024-01-31T00:37:24.248481", "status": "completed"}
hv.Overlay([fan_chart_quantile(df_normalized, c, median_only=True) for c in df_normalized.columns]).opts(title='SSC Other Weekly Balances', ylabel='SSC', legend_opts={'location':'top_left'})

# %% [markdown] papermill={"duration": 0.008976, "end_time": "2024-01-31T00:37:25.040408", "exception": false, "start_time": "2024-01-31T00:37:25.031432", "status": "completed"}
# ### Daily Balances Min Max and Mean

# %% papermill={"duration": 0.018341, "end_time": "2024-01-31T00:37:25.066826", "exception": false, "start_time": "2024-01-31T00:37:25.048485", "status": "completed"}
balance_columns = list(set([c for c in sim_df.columns if 'balance' in c]) - set(system_balances))

# %% papermill={"duration": 0.017687, "end_time": "2024-01-31T00:37:25.094798", "exception": false, "start_time": "2024-01-31T00:37:25.077111", "status": "completed"}
balance_columns

# %% papermill={"duration": 0.330354, "end_time": "2024-01-31T00:37:25.433663", "exception": false, "start_time": "2024-01-31T00:37:25.103309", "status": "completed"}
hv.Overlay([fan_chart_quantile(sim_df, c, median_only=False) for c in balance_columns]).opts(title='SSC Daily Balances Fan Chart Comparison', ylabel='SSC', legend_opts={'location':'top_left'})

# %% [markdown] papermill={"duration": 0.008689, "end_time": "2024-01-31T00:37:25.452986", "exception": false, "start_time": "2024-01-31T00:37:25.444297", "status": "completed"}
# Weekly Balances Bar Chart by Run

# %% papermill={"duration": 0.026466, "end_time": "2024-01-31T00:37:25.488191", "exception": false, "start_time": "2024-01-31T00:37:25.461725", "status": "completed"}
from subspace_model.util import g

# %% papermill={"duration": 0.137239, "end_time": "2024-01-31T00:37:25.636440", "exception": false, "start_time": "2024-01-31T00:37:25.499201", "status": "completed"}
weekly_aggregated_df.hvplot.bar(x='weeks_passed', y=balance_columns, groupby='run', stacked=False, alpha=1, width=1200, height=500, legend='top_right', ylabel='SSC', tools=[hover], ylim=(0,None), title='SSC Weekly Balances Compared', rot=90, color=[column_colors[c] for c in balance_columns]).opts(multi_level=False)

# %% papermill={"duration": 0.152261, "end_time": "2024-01-31T00:37:25.798095", "exception": false, "start_time": "2024-01-31T00:37:25.645834", "status": "completed"}
weekly_aggregated_df.hvplot.bar(x='run', y=balance_columns, groupby='weeks_passed', stacked=False, alpha=1, width=1200, height=500, legend='top_right', ylabel='SSC', tools=[hover], ylim=(0,None), title='SSC Weekly Balances Compared', rot=90, color=[column_colors[c] for c in balance_columns]).opts(multi_level=False)

# %% [markdown] papermill={"duration": 0.009138, "end_time": "2024-01-31T00:37:25.818492", "exception": false, "start_time": "2024-01-31T00:37:25.809354", "status": "completed"}
# Box Charts

# %% papermill={"duration": 0.027494, "end_time": "2024-01-31T00:37:25.855284", "exception": false, "start_time": "2024-01-31T00:37:25.827790", "status": "completed"}
box_df = sim_df.set_index(['weeks_passed', 'run'])[balance_columns]
box_df.describe()

# %% papermill={"duration": 0.518358, "end_time": "2024-01-31T00:37:26.383257", "exception": false, "start_time": "2024-01-31T00:37:25.864899", "status": "completed"}
box_df.melt().hvplot.violin(y='value', by='variable', c='variable', legend='top_right', width=1200, height=500, title=f'SSC Balances Violin Chart by Across All Weeks and All Runs', cmap=column_colors, ylim=(0,box_df.max().max()*0.75))

# %% papermill={"duration": 0.348618, "end_time": "2024-01-31T00:37:26.743869", "exception": false, "start_time": "2024-01-31T00:37:26.395251", "status": "completed"}
box_df.reset_index().drop('weeks_passed',axis=1).melt(id_vars=['run']).hvplot.violin(y='value', by='variable', c='variable', groupby='run', legend='top_right', width=1200, height=500, title=f'SSC Balances Violin Chart Across Weeks by Run', cmap=column_colors, ylim=(0,box_df.max().max()*0.75))

# %% papermill={"duration": 0.311156, "end_time": "2024-01-31T00:37:27.072327", "exception": false, "start_time": "2024-01-31T00:37:26.761171", "status": "completed"}
violin_plot = box_df.reset_index().drop('run',axis=1).melt(id_vars=['weeks_passed']).hvplot.violin(y='value', by='variable', c='variable', groupby='weeks_passed', legend='top_right', width=1200, height=500, title=f'SSC Balances Violin Chart Across Runs by Week', cmap=column_colors, ylim=(0,box_df.max().max()*0.75))
violin_plot

# %% papermill={"duration": 0.012693, "end_time": "2024-01-31T00:37:27.115327", "exception": false, "start_time": "2024-01-31T00:37:27.102634", "status": "completed"}
