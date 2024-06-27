from subspace_model.logic import *
from typing import Callable
from copy import deepcopy
import logging

logger = logging.getLogger("subspace-digital-twin")


# Non processed blocks

_SUBSPACE_MODEL_BLOCKS: list[dict] = [
    {
        "label": "Time Tracking",
        "ignore": False,
        "desc": "Updates the time in the system",
        "policies": {"evolve_time": p_evolve_time},
        "variables": {
            "delta_days": replace_suf,
            "days_passed": add_suf,
            "delta_blocks": replace_suf,
            "blocks_passed": add_suf,
        },
    },
    {
        "label": "Reference Subsidy",
        "ignore": False,
        "policies": {},
        "variables": {
            "reference_subsidy": s_reference_subsidy,
        },
    },
    {
        "label": "Environmental Processes",
        "ignore": False,
        "policies": {"block_utilization": p_block_utilization},
        "variables": {
            "average_priority_fee": s_average_priority_fee,
            "average_compute_weight_per_tx": s_average_compute_weight_per_tx,
            "transaction_count": replace_suf,
            "average_transaction_size": replace_suf,
            "average_compute_weight_per_bundle": s_average_compute_weight_per_bundle,
            "bundle_count": s_bundle_count,
            "block_utilization": replace_suf
        },
    },
    {
        "label": "Archival Process",
        "policies": {"archival": p_archive},
        "variables": {
            "blockchain_history_size": add_suf,
            "buffer_size": add_suf,
        },
    },
    {
        "label": "Sector Onboarding",
        "policies": {"sector_onboarding": p_pledge_sectors},
        "variables": {
            "total_space_pledged": add_suf,
        },
    },
    {
        "label": "Issuance Rewards",
        "ignore": False,
        "policies": {
            "issuance_reward": p_reward,
        },
        "variables": {
            "reward_issuance_balance": add_suf,
            "farmers_balance": add_suf,

            "block_reward": replace_suf,
            "reward_to_voters": replace_suf,
            "reward_to_proposer": replace_suf,
        },
    },
    {
        "label": "Storage Fees",
        "ignore": False,
        "policies": {"storage_fees": p_storage_fees},
        "variables": {
            # Fee Calculation
            "replication_factor": replace_suf,
            "storage_fee_in_shannon_per_bytes": replace_suf,
            "extrinsic_length_in_bytes": replace_suf,
            "storage_fee_volume": replace_suf,
        },
    },
    {
        "label": "Compute Fees",
        "ignore": False,
        "policies": {"compute_fees": p_compute_fees},
        "variables": {
            # Compute fee calculations
            "target_block_delta": replace_suf,
            "targeted_adjustment_parameter": replace_suf,
            "compute_fee_multiplier": replace_suf,
            "tx_compute_weight": replace_suf,
            "compute_fee_volume": replace_suf,
            "priority_fee_volume": replace_suf,
            # Fees and rewards distribution
            "farmers_balance": add_suf,
            "nominators_balance": add_suf,
            "operators_balance": add_suf
        },
    },
    {
        "label": "Direct Allocations",
        "ignore": False,
        "policies": {"unvest": p_unvest},
        "variables": {
            "vesting_balance": add_suf,
            "farmers_balance": add_suf,
            "allocated_tokens": replace_suf,
            "allocated_tokens_investors": replace_suf,
            "allocated_tokens_founders": replace_suf,
            "allocated_tokens_team": replace_suf,
            "allocated_tokens_advisors": replace_suf,
            "allocated_tokens_vendors": replace_suf,
            "allocated_tokens_ambassadors": replace_suf,

        },
    },
    {
        "label": "Slash",
        "ignore": False,
        "policies": {"slash": p_slash},
        "variables": {
            "staking_pool_balance": add_suf,
            "operator_pool_shares": add_suf,
            "burnt_balance": add_suf,
        },
    },
    {
        "label": "Staking / Unstaking",
        "ignore": False,
        "policies": {
            "staking": p_staking,
        },
        "variables": {
            "operators_balance": add_suf,
            "nominators_balance": add_suf,
            "staking_pool_balance": add_suf,
            "operator_pool_shares": add_suf,
            "nominator_pool_shares": add_suf,
        },
    },
    {
        "label": "Transfers",
        "ignore": False,
        "policies": {"transfers": p_transfers},
        "variables": {
            "operators_balance": add_suf,
            "nominators_balance": add_suf,
            "farmers_balance": add_suf,
        },
    },
    {
        "label": "Metrics",
        "policies": {},
        "variables": {
            "circulating_supply": lambda _1, _2, _3, state, _5: (
                "circulating_supply",
                circulating_supply(state),
            ),
            "user_supply": lambda _1, _2, _3, state, _5: (
                "user_supply",
                user_supply(state),
            ),
            "earned_supply": lambda _1, _2, _3, state, _5: (
                "user_supply",
                earned_supply(state),
            ),
            "issued_supply": lambda _1, _2, _3, state, _5: (
                "issued_supply",
                issued_supply(state),
            ),
            "earned_minus_burned_supply": lambda _1, _2, _3, state, _5: (
                "user_supply",
                earned_minus_burned_supply(state),
            ),
            "total_supply": lambda _1, _2, _3, state, _5: (
                "total_supply",
                total_supply(state),
            ),
            "sum_of_stocks": lambda _1, _2, _3, state, _5: (
                "sum_of_stocks",
                sum_of_stocks(state),
            ),
            "storage_fee_per_rewards": lambda _1, _2, _3, state, _5: (
                "storage_fee_per_rewards",
                storage_fee_per_rewards(state),
            ),
            "community_owned_supply": lambda params, _2, _3, state, _5: (
                "community_owned_supply",
                community_owned_supply(state, params),
            ),
            "cumm_rewards": s_cumm_generic("block_reward", "cumm_rewards", nan_value=0.0),
            "cumm_storage_fees_to_farmers": s_cumm_generic("storage_fee_volume", "cumm_storage_fees_to_farmers"),
            "cumm_compute_fees_to_farmers": s_cumm_compute_fee_to_farmers
        },
    },
]


# Post Processing

blocks: list[dict] = []
for block in [b for b in _SUBSPACE_MODEL_BLOCKS if b.get("ignore", False) != True]:
    _block = deepcopy(block)
    for variable, suf in block.get("variables", {}).items():
        if suf == add_suf:
            _block["variables"][variable] = add_suf(variable)
        elif suf == replace_suf:
            _block["variables"][variable] = replace_suf(variable)
        else:
            pass
    blocks.append(_block)

SUBSPACE_MODEL_BLOCKS = deepcopy(blocks)

logger.debug("SUBSPACE_MODEL_BLOCKS: \n%s", [
             b["label"] for b in SUBSPACE_MODEL_BLOCKS])
