from dataclasses import dataclass

from numpy import nan

from subspace_model.const import *
from subspace_model.experiments.logic import (
    DEFAULT_ISSUANCE_FUNCTION,
    DEFAULT_REFERENCE_SUBSIDY_COMPONENTS,
    MAINNET_REFERENCE_SUBSIDY_COMPONENTS,
    DEFAULT_SLASH_FUNCTION,
    MAGNITUDE,
    NORMAL_GENERATOR,
    POISSON_GENERATOR,
    POSITIVE_INTEGER,
    SUPPLY_ISSUED,
    TRANSACTION_COUNT_PER_DAY_FUNCTION_CONSTANT_UTILIZATION_50,
    TRANSACTION_COUNT_PER_DAY_FUNCTION_GROWING_UTILIZATION_TWO_YEARS,
    WEEKLY_VARYING,
)

def operator_stake_per_ts_function(p: SubspaceModelParams, s: SubspaceModelState):
    return 0.01


def nominator_stake_per_ts_function(p: SubspaceModelParams, s: SubspaceModelState):
    return 0.01

def compute_weights_per_tx_function(p: SubspaceModelParams, s: SubspaceModelState):
    return 60_000_000

DEFAULT_PARAMS = SubspaceModelParams(
    # Meta
    label="standard",
    environmental_label="standard",
    timestep_in_days=1,

    # Mechanism Parameters
    issuance_function=DEFAULT_ISSUANCE_FUNCTION,
    slash_function=DEFAULT_SLASH_FUNCTION, 
    reference_subsidy_components=DEFAULT_REFERENCE_SUBSIDY_COMPONENTS,
    issuance_function_constant=1,
    utilization_ratio_smooth_num_blocks=100,

    # Implementation parameters
    block_time_in_seconds=BLOCK_TIME,
    archival_depth=ARCHIVAL_DEPTH,
    archival_buffer_segment_size=SEGMENT_SIZE,
    header_size=6_500,  # how much data does every block contain on top of txs: signature, solution, consensus logs, etc. + votes + PoT
    min_replication_factor=50,
    max_block_size=int(3.75 * MIB_IN_BYTES),  # 3.75 MiB
    weight_to_fee=1 * SHANNON_IN_CREDITS,

    # Economic Parameters
    reward_recipients=10,
    reward_proposer_share=0.3,  # NOTE: to sweep
    max_credit_supply=MAX_CREDIT_ISSUANCE,  # TODO:
    credit_supply_definition=SUPPLY_ISSUED, # TODO: Set in stone the def
    community_vested_supply_fraction=0.225,

    # Fees & Taxes
    fund_tax_on_proposer_reward=0.0,  # TODO: assume
    fund_tax_on_storage_fees=1 / 10, # TODO: assume
    compute_fees_to_farmers=0.0,  # NOTE: to sweep
    compute_fees_tax_to_operators=0.05,  # or `nomination_tax`

    # Slash Parameters
    slash_to_fund=0.0,
    slash_to_holders=0.05,

    # Other
    initial_community_owned_supply_pct_of_max_credits=(1/33), # TODO


    # Behavioral Parameters Between 0 and 1
    operator_stake_per_ts_function=operator_stake_per_ts_function,
    nominator_stake_per_ts_function=nominator_stake_per_ts_function,
    transfer_farmer_to_holder_per_day_function=lambda p, s: 0.05,
    transfer_operator_to_holder_per_day_function=lambda p, s: 0.05,
    transfer_holder_to_nominator_per_day_function=lambda p, s: 0.01,
    transfer_holder_to_operator_per_day_function=lambda p, s: 0.01,

    # Environmental Parameters (Integer positive in [0,inf])
    ## Environmental: Fees
    priority_fee_function=lambda p, s: 0,

    ## Enviromental: Compute Weights per Tx
    compute_weights_per_tx_function=compute_weights_per_tx_function,
    min_compute_weights_per_tx=6_000_000,  # TODO
    compute_weight_per_bundle_function=lambda p, s: 10_000_000_000,
    min_compute_weights_per_bundle=2_000_000_000,  # TODO

    ## Environmental: Tx Sizes
    transaction_size_function=lambda p, s: 256,
    min_transaction_size=100,  # TODO
    bundle_size_function=lambda p, s: 1500,
    min_bundle_size=250,  # TODO

    ## Environmental: Tx Count
    transaction_count_per_day_function=TRANSACTION_COUNT_PER_DAY_FUNCTION_CONSTANT_UTILIZATION_50,
    bundle_count_per_day_function=lambda p, s: 6 * BLOCKS_PER_DAY,

    ## Environmental: Slash Count
    slash_per_day_function=lambda p, s: 0.1,

    ## Environmental: Space Pledged per Time
    new_sectors_per_day_function=lambda p, s: 1000
)

GOVERNANCE_SURFACE = {
        "reference_subsidy_components": MAINNET_REFERENCE_SUBSIDY_COMPONENTS(),
        "reward_proposer_share": [1/10, 1/3],
        "weight_to_fee": [1 * SHANNON_IN_CREDITS, 100 * SHANNON_IN_CREDITS, 1_000 * SHANNON_IN_CREDITS, 10_000 * SHANNON_IN_CREDITS],
        }

def predictable_trajectory(value):
    mu = value
    sigma = 0.3 * mu
    generator = NORMAL_GENERATOR(mu, sigma)
    return generator

def high_volatility_trajectory(value):
    mu = value
    sigma = 5 * mu
    generator = NORMAL_GENERATOR(mu, sigma)
    return generator

def predictable_trajectory_with_instantaneous_shocks(value):
    mu = value
    sigma = 0.3 * mu
    generator = NORMAL_INSTANTANEOUS_SHOCK_GENERATOR(mu, sigma, N=N)
    return generator

def predictable_trajectory_with_instantaneous_shocks(value):
    mu = value
    sigma = 0.3 * mu
    generator = NORMAL_SUSTAINED_SHOCK_GENERATOR(mu, sigma, N=N, M=M)
    return generator



def scenario_groups(values, N=13*BLOCKS_PER_WEEK, M=7*BLOCKS_PER_DAY):
    groups = [predictable_trajectory, high_volatility_trajectory, predictable_trajectory_with_instantaneous_shocks, predictable_trajectory_with_sustained_shocks]
    results = []
    for group in groups:
        for value in values:
            results.append(group(value))
    return results

ENVIRONMENTAL_SCENARIOS = {
        "SG1": {
            "dao_utilization_ratio": scenario_groups([0.005, 0.01, 0.02]),
            "dao_newly_pledged_space": scenario_groups([0.25*PB_IN_BYTES, 1*PB_IN_BYTES, 5*PB_IN_BYTES]),
            "dao_priority_fee_per_time": scenario_groups([0]),
            "dao_slash_per_day": scenario_groups([0]),
            "operator_stake_per_ts_function": scenario_groups([0, 0.1, 1]),
            "nominator_stake_per_ts_function": scenario_groups([0, 0.1, 1]),
            "transfer_farmer_to_holder_per_day_function": scenario_groups([1]),
            "transfer_operator_to_holder_per_day_function": scenario_groups([0, 0.1, 1]),
            "transfer_holder_to_nominator_per_day_function": scenario_groups([0, 0.05]),
            "transfer_holder_to_operator_per_day_function": scenario_groups([0, 0.05]),
            }
        }

ENVIRONMENTAL_SCENARIOS = {
    "stochastic": {
        # Behavioral Parameters Between 0 and 1
        "operator_stake_per_ts_function": MAGNITUDE(NORMAL_GENERATOR(0.01, 0.02)),
        "nominator_stake_per_ts_function": MAGNITUDE(NORMAL_GENERATOR(0.01, 0.02)),
        "transfer_farmer_to_holder_per_day_function": MAGNITUDE(
            NORMAL_GENERATOR(0.05, 0.05)
        ),
        "transfer_operator_to_holder_per_day_function": MAGNITUDE(
            NORMAL_GENERATOR(0.05, 0.05)
        ),
        "transfer_holder_to_nominator_per_day_function": MAGNITUDE(
            NORMAL_GENERATOR(0.01, 0.02)
        ),
        "transfer_holder_to_operator_per_day_function": MAGNITUDE(
            NORMAL_GENERATOR(0.01, 0.02)
        ),
        # Environmental Parameters (Integer positive in [0,inf])
        "environmental_label": "stochastic",
        "priority_fee_function": POSITIVE_INTEGER(NORMAL_GENERATOR(0, 0.001)),
        "compute_weights_per_tx_function": POSITIVE_INTEGER(
            NORMAL_GENERATOR(60_000_000, 15_000_000)
        ),
        "compute_weight_per_bundle_function": POSITIVE_INTEGER(
            NORMAL_GENERATOR(10_000_000_000, 5_000_000_000)
        ),
        "transaction_size_function": POSITIVE_INTEGER(NORMAL_GENERATOR(256, 100)),
        "bundle_size_function": POSITIVE_INTEGER(NORMAL_GENERATOR(1500, 1000)),
        "transaction_count_per_day_function": POISSON_GENERATOR(1 * BLOCKS_PER_DAY),
        "bundle_count_per_day_function": POISSON_GENERATOR(6 * BLOCKS_PER_DAY),
        "slash_per_day_function": POISSON_GENERATOR(0.1),
        "new_sectors_per_day_function": POSITIVE_INTEGER(NORMAL_GENERATOR(1000, 500)),
    },
    "weekly-varying": {
        "environmental_label": "weekly-varying",
        "priority_fee_function": WEEKLY_VARYING,
    },
    "constant-utilization": {
        "environmental_label": "constant-utilization",
        "transaction_count_per_day_function": TRANSACTION_COUNT_PER_DAY_FUNCTION_CONSTANT_UTILIZATION_50,
    },
    "growing-utilization": {
        "environmental_label": "growing-utilization",
        "transaction_count_per_day_function": TRANSACTION_COUNT_PER_DAY_FUNCTION_GROWING_UTILIZATION_TWO_YEARS,
    },
}
