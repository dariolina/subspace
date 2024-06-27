from typing import Callable, Dict, List, Any
from numpy import nan

from subspace_model.const import *
from subspace_model.types import SubspaceModelParams, SubspaceModelState
from subspace_model.experiments.logic import predictable_trajectory

from subspace_model.experiments.logic import (
    DEFAULT_REFERENCE_SUBSIDY_COMPONENTS,
    MAINNET_REFERENCE_SUBSIDY_COMPONENTS,
    REFERENCE_SUBSIDY_MAINNET_TWO_COMPONENTS,
    DEFAULT_SLASH_FUNCTION,
    MAGNITUDE,
    NORMAL_GENERATOR,
    POISSON_GENERATOR,
    POSITIVE_INTEGER,
    SUPPLY_ISSUED, 
    CIRCULATING_SUPPLY,
    TRANSACTION_COUNT_PER_DAY_FUNCTION_CONSTANT_UTILIZATION_50,
    TRANSACTION_COUNT_PER_DAY_FUNCTION_GROWING_UTILIZATION_TWO_YEARS,
    TRANSACTION_COUNT_PER_DAY_FUNCTION_FROM_UTILIZATION_RATIOS,
    WEEKLY_VARYING,
    SCENARIO_GROUPS,
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
    slash_function=DEFAULT_SLASH_FUNCTION,
    reference_subsidy_components=REFERENCE_SUBSIDY_MAINNET_TWO_COMPONENTS,
    utilization_ratio_smooth_num_blocks=100,
    # Implementation parameters
    block_time_in_seconds=BLOCK_TIME,
    archival_depth=ARCHIVAL_DEPTH,
    archival_buffer_segment_size=SEGMENT_SIZE,
    header_size=6_500,  # how much data does every block contain on top of txs: signature, solution, consensus logs, etc. + votes + PoT
    min_replication_factor=50,
    max_block_size=int(3.75 * MIB_IN_BYTES),  # 3.75 MiB
    weight_to_fee=100_000 * SHANNON_IN_CREDITS,
    # Economic Parameters
    reward_recipients=10,
    reward_proposer_share=0.3,  # NOTE: to sweep
    max_credit_supply=MAX_CREDIT_ISSUANCE,
    credit_supply_definition=CIRCULATING_SUPPLY,
    # Fees & Taxes
    compute_fees_to_farmers=0.0,  # NOTE: to sweep
    compute_fees_tax_to_operators=0.05,  # or `nomination_tax`
    # Slash Parameters
    slash_to_farmers=0.05,
    # Other
    initial_community_owned_supply_pct_of_max_credits=0.135, # XXX
    initial_space_pledged = 10*PB_IN_BYTES,
    initial_history_size=20*SEGMENT_HISTORY_SIZE,
    # Behavioral Parameters Between 0 and 1
    operator_stake_per_ts_function=operator_stake_per_ts_function,
    nominator_stake_per_ts_function=nominator_stake_per_ts_function,
    transfer_operator_to_farmer_per_day_function=lambda p, s: 0.05,
    transfer_farmer_to_nominator_per_day_function=lambda p, s: 0.01,
    transfer_farmer_to_operator_per_day_function=lambda p, s: 0.01,
    # Environmental Parameters (Integer positive in [0,inf])
    ## Environmental: Fees
    priority_fee_function=lambda p, s: 0,
    ## Enviromental: Compute Weights per Tx
    compute_weights_per_tx_function=compute_weights_per_tx_function,
    min_compute_weights_per_tx=45_798_000,  # XXX
    compute_weight_per_bundle_function=lambda p, s: 125_000_000_000,
    min_compute_weights_per_bundle=824_000_000,  # XXX
    ## Environmental: Tx Sizes
    transaction_size_function=lambda p, s: 256,
    min_transaction_size=100,  # XXX
    bundle_size_function=lambda p, s: 1500,
    min_bundle_size=250,  # XXX
    ## Environmental: Tx Count
    bundle_count_per_day_function=lambda p, s: 6 * BLOCKS_PER_DAY,
    transaction_count_per_day_function=TRANSACTION_COUNT_PER_DAY_FUNCTION_FROM_UTILIZATION_RATIOS,
    ## Environmental: Slash Count
    slash_per_day_function=lambda p, s: 0,
    ## Environmental: Space Pledged per Time
    newly_pledged_space_per_day_function=lambda p, s: 5*PB_IN_BYTES,
    utilization_ratio=0.01,
    utilization_ratio_function=MAGNITUDE(SCENARIO_GROUPS([0.01])[0])
)


GOVERNANCE_SURFACE: Dict[str, List] = {
    "reference_subsidy_components": MAINNET_REFERENCE_SUBSIDY_COMPONENTS(),
    "reward_proposer_share": [1 / 10, 1 / 3],
    "weight_to_fee": [
        1 * SHANNON_IN_CREDITS,
        100 * SHANNON_IN_CREDITS,
        1_000 * SHANNON_IN_CREDITS,
        10_000 * SHANNON_IN_CREDITS,
    ],
}


ENVIRONMENTAL_SCENARIOS: Dict[str, List[Callable]] = {
    "utilization_ratio_function": [
        MAGNITUDE(generator) for generator in SCENARIO_GROUPS([0.2, 0.01, 0.02])
    ],
    "priority_fee_function": [
        MAGNITUDE(generator) for generator in SCENARIO_GROUPS([0])
    ],
    "slash_per_day_function": [
        MAGNITUDE(generator) for generator in SCENARIO_GROUPS([0])
    ],
    "operator_stake_per_ts_function": [
        NORMAL_GENERATOR(0.01, 0.02)
    ],
    "nominator_stake_per_ts_function": [
        NORMAL_GENERATOR(0.01, 0.02)
    ],
    "transfer_operator_to_farmer_per_day_function": [
        MAGNITUDE(generator) for generator in SCENARIO_GROUPS([0.1])
    ],
    "transfer_farmer_to_nominator_per_day_function": [
        MAGNITUDE(generator) for generator in SCENARIO_GROUPS([0.025])
    ],
    "transfer_farmer_to_operator_per_day_function": [
        MAGNITUDE(generator) for generator in SCENARIO_GROUPS([0.025])
    ],
}


SPECIAL_ENVIRONMENTAL_SCENARIOS = {
    "stochastic": {
        # Behavioral Parameters Between 0 and 1
        "operator_stake_per_ts_function": NORMAL_GENERATOR(0.01, 0.02),
        "nominator_stake_per_ts_function": NORMAL_GENERATOR(0.01, 0.02),
        "transfer_operator_to_farmer_per_day_function": MAGNITUDE(
            NORMAL_GENERATOR(0.05, 0.05)
        ),
        "transfer_farmer_to_nominator_per_day_function": MAGNITUDE(
            NORMAL_GENERATOR(0.01, 0.02)
        ),
        "transfer_farmer_to_operator_per_day_function": MAGNITUDE(
            NORMAL_GENERATOR(0.01, 0.02)
        ),
        # Environmental Parameters (Integer positive in [0,inf])
        "environmental_label": "stochastic",
        "priority_fee_function": POSITIVE_INTEGER(NORMAL_GENERATOR(0, 0.001)),
        "compute_weights_per_tx_function": POSITIVE_INTEGER(
            NORMAL_GENERATOR(80_000_000, 15_000_000)
        ),
        "compute_weight_per_bundle_function": POSITIVE_INTEGER(
            NORMAL_GENERATOR(125_000_000_000, 50_000_000_000)
        ),
        "transaction_size_function": POSITIVE_INTEGER(NORMAL_GENERATOR(512, 256)),
        "bundle_size_function": POSITIVE_INTEGER(NORMAL_GENERATOR(1500, 1000)),
        "transaction_count_per_day_function": POISSON_GENERATOR(1 * BLOCKS_PER_DAY),
        "bundle_count_per_day_function": POISSON_GENERATOR(6 * BLOCKS_PER_DAY),
        "slash_per_day_function": POISSON_GENERATOR(0.0001),
        "new_sectors_per_day_function": POSITIVE_INTEGER(NORMAL_GENERATOR(5_000_000, 5_000_000)),
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
