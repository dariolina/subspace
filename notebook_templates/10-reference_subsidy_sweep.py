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

# %% [markdown] papermill={"duration": 0.006216, "end_time": "2024-01-31T00:37:29.330007", "exception": false, "start_time": "2024-01-31T00:37:29.323791", "status": "completed"}
# # Subspace Digital Twin, Initial Conditions Run
#
# *Shawn Anderson, January 2024*
#
# In this notebook, we examine medianl behavior over the first 90 days.

# %% [markdown] papermill={"duration": 0.004427, "end_time": "2024-01-31T00:37:29.342035", "exception": false, "start_time": "2024-01-31T00:37:29.337608", "status": "completed"}
# ## Part 1. Dependences & Set-up

# %% [markdown] papermill={"duration": 0.002372, "end_time": "2024-01-31T00:37:29.347022", "exception": false, "start_time": "2024-01-31T00:37:29.344650", "status": "completed"}
# Autoreload modules while developing.

# %% papermill={"duration": 1.402484, "end_time": "2024-01-31T00:37:30.751861", "exception": false, "start_time": "2024-01-31T00:37:29.349377", "status": "completed"}
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

from subspace_model.util import g

# %% [markdown] papermill={"duration": 0.006671, "end_time": "2024-01-31T08:17:08.602231", "exception": false, "start_time": "2024-01-31T08:17:08.595560", "status": "completed"}
# ## Part 2. Load Simulation Data

# %% [markdown] papermill={"duration": 0.00683, "end_time": "2024-01-31T08:17:08.617129", "exception": false, "start_time": "2024-01-31T08:17:08.610299", "status": "completed"}
# Load the simulation results data.

# %% papermill={"duration": 0.021693, "end_time": "2024-01-31T08:17:08.644912", "exception": false, "start_time": "2024-01-31T08:17:08.623219", "status": "completed"}
import glob
import os

def load_latest_simulation(simulation_name):
    files = glob.glob(f"../data/simulations/{simulation_name}-*.pkl.gz")
    latest_file = max(files, key=os.path.getctime)

    print(f"Loading Latest File: {latest_file}")
    df = pd.read_pickle(latest_file)
    df = df.drop(['timestep', 'simulation', 'subset', 'timestep_in_days', 'block_time_in_seconds', 'delta_days', 'delta_blocks'], axis=1)
    return df


# %% papermill={"duration": 0.06953, "end_time": "2024-01-31T08:17:08.720237", "exception": false, "start_time": "2024-01-31T08:17:08.650707", "status": "completed"}
sim_df = load_latest_simulation("reference_subsidy_sweep")
sim_df

# %% papermill={"duration": 0.0231, "end_time": "2024-01-31T08:17:08.749916", "exception": false, "start_time": "2024-01-31T08:17:08.726816", "status": "completed"}
# sim_df = pd.read_pickle(
#     "../data/simulations/reference_subsidy_sweep-2024-01-30_11-07-21.pkl.gz"
# ).drop(['timestep', 'simulation', 'subset', 'timestep_in_days', 'block_time_in_seconds', 'delta_days', 'delta_blocks'], axis=1)

# %% papermill={"duration": 0.042732, "end_time": "2024-01-31T08:17:08.799469", "exception": false, "start_time": "2024-01-31T08:17:08.756737", "status": "completed"}
sim_df.head(5)

# %% [markdown] papermill={"duration": 0.013319, "end_time": "2024-01-31T08:17:08.825605", "exception": false, "start_time": "2024-01-31T08:17:08.812286", "status": "completed"}
# Simulation Runs.

# %% papermill={"duration": 0.034271, "end_time": "2024-01-31T08:17:08.874627", "exception": false, "start_time": "2024-01-31T08:17:08.840356", "status": "completed"}
sim_df.groupby(['run', 'label', 'environmental_label']).size().reset_index(name='Days').head()

# %% [markdown] papermill={"duration": 0.012138, "end_time": "2024-01-31T08:17:08.901732", "exception": false, "start_time": "2024-01-31T08:17:08.889594", "status": "completed"}
# ### Coloring Metrics
# Use a constant mapping from columns to colors

# %% papermill={"duration": 0.263454, "end_time": "2024-01-31T08:17:09.179476", "exception": false, "start_time": "2024-01-31T08:17:08.916022", "status": "completed"}
color_palette = Category20
# columns_to_color = sorted(list(set(sim_df.columns) - {'environmental_label', 'label', 'run', 'blocks_passed', 'days_passed'}))
columns_to_color = sim_df.columns
if color_palette == Turbo256:
    column_colors = dict(zip(columns_to_color, [color_palette[int(i)] for i in np.linspace(0,len(color_palette)-1, len(columns_to_color))]))

if color_palette == Category20:
    column_colors = {col: Category20[20][i%20] for i, col in enumerate(columns_to_color)}


sim_df.count().to_frame().T.hvplot.bar(y=columns_to_color, color=[column_colors[c] for c in columns_to_color], rot=90, width=1400, height=500, title='Column Color Map', fontscale=1.4, yaxis=None)


# %% papermill={"duration": 0.03437, "end_time": "2024-01-31T08:17:09.221250", "exception": false, "start_time": "2024-01-31T08:17:09.186880", "status": "completed"}
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



# %% [markdown] papermill={"duration": 0.007473, "end_time": "2024-01-31T08:17:09.236361", "exception": false, "start_time": "2024-01-31T08:17:09.228888", "status": "completed"}
# ### KPIs

# %% papermill={"duration": 0.024543, "end_time": "2024-01-31T08:17:09.268126", "exception": false, "start_time": "2024-01-31T08:17:09.243583", "status": "completed"}
sim_df['issuance'] = sim_df['block_reward'] + sim_df['reference_subsidy']

sim_df['fees'] = sim_df['compute_fee_volume'] + sim_df['storage_fee_volume']

fees_and_issuance = ['compute_fee_volume','storage_fee_volume', 'fees', 'block_reward', 'reference_subsidy', 'issuance']

# %% papermill={"duration": 0.031197, "end_time": "2024-01-31T08:17:09.306698", "exception": false, "start_time": "2024-01-31T08:17:09.275501", "status": "completed"}
# Compute Fees and Storage Fees

# The dynamics of storage fees vs issuance. Who will dominate at the beginning, storage fees or issues rewards? Note that this is a metric.
# Another metrics of interest, general revenue per timestep, farmers, proposers, voters, and data blocks
# revenue = proposer_reward + storage_fees. For data blocks and voters you only have rewards not fees. Farmers is the sum of those three.
# The above topics are what has been discussed and therefor are higher priority than the stocks. 

# %% papermill={"duration": 0.269027, "end_time": "2024-01-31T08:17:09.583552", "exception": false, "start_time": "2024-01-31T08:17:09.314525", "status": "completed"}
color_palette = Category20
# columns_to_color = sorted(list(set(sim_df.columns) - {'environmental_label', 'label', 'run', 'blocks_passed', 'days_passed'}))
columns_to_color = sim_df.columns
if color_palette == Turbo256:
    column_colors = dict(zip(columns_to_color, [color_palette[int(i)] for i in np.linspace(0,len(color_palette)-1, len(columns_to_color))]))

if color_palette == Category20:
    column_colors = {col: Category20[20][i%20] for i, col in enumerate(columns_to_color)}


sim_df.count().to_frame().T.hvplot.bar(y=columns_to_color, color=[column_colors[c] for c in columns_to_color], rot=90, width=1400, height=500, title='Column Color Map', fontscale=1.4, yaxis=None)

# %% [markdown] papermill={"duration": 0.007376, "end_time": "2024-01-31T08:17:09.598583", "exception": false, "start_time": "2024-01-31T08:17:09.591207", "status": "completed"}
# ### Balances and Supplies

# %% papermill={"duration": 0.028049, "end_time": "2024-01-31T08:17:09.634202", "exception": false, "start_time": "2024-01-31T08:17:09.606153", "status": "completed"}
system_balances = ['vesting_balance', 'reward_issuance_balance']
agent_balances = [
    'farmers_balance',
    'operators_balance',
    'nominators_balance',
    'holders_balance',
]
agent_pool_balances = ['staking_pool_balance']
protocol_treasury_balances = ['fund_balance']
other_balances = list(set([c for c in sim_df.columns if 'balance' in c]) - set(system_balances + agent_balances + agent_pool_balances + protocol_treasury_balances) )
supply_columns = list({c for c in sim_df.columns if 'supply' in c} - {'max_credit_supply', 'issued_supply', 'total_supply'})
balance_columns = list(set([c for c in sim_df.columns if 'balance' in c]) - set(system_balances))

# %% papermill={"duration": 0.027302, "end_time": "2024-01-31T08:17:09.669151", "exception": false, "start_time": "2024-01-31T08:17:09.641849", "status": "completed"}
system_balances

# %% papermill={"duration": 0.022893, "end_time": "2024-01-31T08:17:09.700239", "exception": false, "start_time": "2024-01-31T08:17:09.677346", "status": "completed"}
agent_balances

# %% papermill={"duration": 0.023792, "end_time": "2024-01-31T08:17:09.734393", "exception": false, "start_time": "2024-01-31T08:17:09.710601", "status": "completed"}
agent_pool_balances

# %% papermill={"duration": 0.025267, "end_time": "2024-01-31T08:17:09.767505", "exception": false, "start_time": "2024-01-31T08:17:09.742238", "status": "completed"}
protocol_treasury_balances

# %% papermill={"duration": 0.023173, "end_time": "2024-01-31T08:17:09.798535", "exception": false, "start_time": "2024-01-31T08:17:09.775362", "status": "completed"}
other_balances

# %% papermill={"duration": 0.022609, "end_time": "2024-01-31T08:17:09.828956", "exception": false, "start_time": "2024-01-31T08:17:09.806347", "status": "completed"}
supply_columns

# %% papermill={"duration": 0.022744, "end_time": "2024-01-31T08:17:09.859454", "exception": false, "start_time": "2024-01-31T08:17:09.836710", "status": "completed"}
balance_columns

# %% papermill={"duration": 0.026633, "end_time": "2024-01-31T08:17:09.893783", "exception": false, "start_time": "2024-01-31T08:17:09.867150", "status": "completed"}
balance_columns

# %% papermill={"duration": 0.023625, "end_time": "2024-01-31T08:17:09.926145", "exception": false, "start_time": "2024-01-31T08:17:09.902520", "status": "completed"}
supply_columns

# %% papermill={"duration": 0.02561, "end_time": "2024-01-31T08:17:09.959575", "exception": false, "start_time": "2024-01-31T08:17:09.933965", "status": "completed"}
fees_and_issuance

# %% papermill={"duration": 0.033531, "end_time": "2024-01-31T08:17:10.001925", "exception": false, "start_time": "2024-01-31T08:17:09.968394", "status": "completed"}
# balance_columns = fees_and_issuance
# balance_columns = supply_columns

# %% papermill={"duration": 0.032984, "end_time": "2024-01-31T08:17:10.043305", "exception": false, "start_time": "2024-01-31T08:17:10.010321", "status": "completed"}
box_df = sim_df.set_index(['days_passed', 'label'])[balance_columns]
box_df

# %% papermill={"duration": 0.036044, "end_time": "2024-01-31T08:17:10.087792", "exception": false, "start_time": "2024-01-31T08:17:10.051748", "status": "completed"}
describe_df = box_df.describe().drop('count')
describe_df

# %% papermill={"duration": 0.055186, "end_time": "2024-01-31T08:17:10.151591", "exception": false, "start_time": "2024-01-31T08:17:10.096405", "status": "completed"}
describe_labels_df = box_df.groupby('label').apply(lambda label: label.describe().drop('count'))
describe_labels_df

# %% papermill={"duration": 0.08472, "end_time": "2024-01-31T08:17:10.244843", "exception": false, "start_time": "2024-01-31T08:17:10.160123", "status": "completed"}
describe_difference_df = pd.DataFrame(describe_labels_df.values - pd.concat([describe_df for i in range(sim_df['label'].nunique())]).values, columns=describe_labels_df.columns, index=describe_labels_df.index)
df = describe_difference_df

def log_scale(val, max_abs_log):
    """ Apply logarithmic scaling to a value. """
    if val == 0:
        return 0
    else:
        return np.sign(val) * np.log(abs(val) + 1) / max_abs_log

def color_scale(val):
    max_abs_val = df.abs().max().max()
    max_abs_log = np.log(max_abs_val + 1)

    scaled_val = log_scale(val, max_abs_log)

    if scaled_val < 0:
        intensity = int(255 * (1 + scaled_val))  # More negative, more red
        return f'background-color: rgb(255, {intensity}, {intensity})'
    elif scaled_val > 0:
        intensity = int(255 * (1 - scaled_val))  # More positive, more green
        return f'background-color: rgb({intensity}, 255, {intensity})'
    else:
        return 'background-color: rgb(255, 255, 255)'

header_styles = [{
    'selector': f'th.col_heading.level0.col{i}',
    'props': [('background-color', column_colors.get(col))]
} for i, col in enumerate(df.columns)]

df.columns.name = 'balance'

describe_difference_df_styled = df.style.map(color_scale).set_table_styles(header_styles)
describe_difference_df_styled

# %% papermill={"duration": 1.227929, "end_time": "2024-01-31T08:17:11.485105", "exception": false, "start_time": "2024-01-31T08:17:10.257176", "status": "completed"}
box_df_melted = box_df.reset_index().drop('days_passed',axis=1).melt(id_vars=['label'])

violin_list = [label.hvplot.violin(y='value', by='variable', c='variable', legend='top_left', width=1200, height=500, title=f'SSC Balances {name}', cmap=column_colors, ylim=(0,box_df.max().max()*0.75)) for name, label in box_df_melted.groupby('label')]

# Combine plots into a single column layout
layout = hv.Layout(violin_list).cols(1)

layout

# %% papermill={"duration": 0.039464, "end_time": "2024-01-31T08:17:11.539156", "exception": false, "start_time": "2024-01-31T08:17:11.499692", "status": "completed"}
[label for name, label in box_df.reset_index().groupby('label')][0]

# %% papermill={"duration": 1.893138, "end_time": "2024-01-31T08:17:13.443415", "exception": false, "start_time": "2024-01-31T08:17:11.550277", "status": "completed"}
line_list = [hv.Overlay([fan_chart_quantile(label, column) for column in label.columns if column not in ['label', 'days_passed']]).opts(title=f'SSC Balances {name}', legend_opts={'location':'top_left'}) for name, label in box_df.reset_index().groupby('label')]
layout = hv.Layout(line_list).cols(1)
layout

# %% papermill={"duration": 1.613757, "end_time": "2024-01-31T08:17:15.081252", "exception": false, "start_time": "2024-01-31T08:17:13.467495", "status": "completed"}
violin_list = [variable.hvplot.violin(y='value', by='label', color=column_colors[name], width=1200, height=500, title=f'SSC Balances {name}', ylim=(0,variable.max()['value'].max()), ylabel=name) for name, variable in box_df_melted.groupby('variable')]

layout = hv.Layout(violin_list).cols(1).opts(shared_axes=False)

layout

# %% papermill={"duration": 0.928905, "end_time": "2024-01-31T08:17:16.030647", "exception": false, "start_time": "2024-01-31T08:17:15.101742", "status": "completed"}
line_list = [variable.hvplot.line(x='days_passed', by='label', y='value', title=name, legend='top_left', line_width=3).opts(legend_opts={'background_fill_color': column_colors[name], 'background_fill_alpha': 0.2}) for name, variable in box_df.reset_index().melt(id_vars=['label', 'days_passed']).groupby('variable')]

layout = hv.Layout(line_list).cols(2).opts(shared_axes=False)
layout

# %% [markdown] papermill={"duration": 0.028686, "end_time": "2024-01-31T08:17:16.083323", "exception": false, "start_time": "2024-01-31T08:17:16.054637", "status": "completed"}
# Definition (per timestep) storage_fees_per_rewards = state['storage_fee_volume'] / state['block_reward']
#
# We are interested in having the (95%, 50%, 5%) quantile distribution over that metric when taking windows of 1 week, 4 weeks and 12 weeks.

# %% papermill={"duration": 0.238559, "end_time": "2024-01-31T08:17:16.347213", "exception": false, "start_time": "2024-01-31T08:17:16.108654", "status": "completed"}
opts = dict(width=800, height=400)
charts = []
for weeks in [1,4,12]:
    sim_df['storage_fee_per_rewards_q1'] = sim_df['storage_fee_per_rewards'].rolling(7*weeks).quantile(0.05)
    sim_df['storage_fee_per_rewards_q2'] = sim_df['storage_fee_per_rewards'].rolling(7*weeks).quantile(0.50)
    sim_df['storage_fee_per_rewards_q3'] = sim_df['storage_fee_per_rewards'].rolling(7*weeks).quantile(0.95)
    
    fan = sim_df.hvplot.area(x='days_passed', y='storage_fee_per_rewards_q1', y2='storage_fee_per_rewards_q3', by='label', stacked=False, hover=False, legend='bottom_right')
    
    median = sim_df.hvplot.line(x='days_passed', y='storage_fee_per_rewards_q2', by='label', alpha=0.8, line_width=4, ylim=(0,None), title=f'Storage Fee Per Rewards 95% Quantile Rolling {weeks} weeks.', legend='bottom_right')
    chart = fan * median
    charts.append(chart.opts(**opts))

# %% papermill={"duration": 0.923605, "end_time": "2024-01-31T08:17:17.305800", "exception": false, "start_time": "2024-01-31T08:17:16.382195", "status": "completed"}
hv.Layout(charts).cols(3)
