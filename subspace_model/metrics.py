import logging

from subspace_model.types import SubspaceModelState, SubspaceModelParams, Credits


def circulating_supply(state: SubspaceModelState) -> Credits:
    return (
        state["operators_balance"]
        + state["nominators_balance"]
        + state["farmers_balance"]
    )


def user_supply(state: SubspaceModelState) -> Credits:
    "All circulating supply tokens can only go to the Staking Pool Balance"
    return circulating_supply(state) + state["staking_pool_balance"]


def earned_supply(state: SubspaceModelState) -> Credits:
    "Should map back to All Issued (and active) Tokens so far"
    return user_supply(state)

def issued_supply(state: SubspaceModelState) -> Credits:
    """
    IssuedSupply = All Vested Tokens + All Issued Tokens so far minus burns
    Can be interpreted as the all tokens in user possession.
    """
    return (
        sum_of_stocks(state) - state["burnt_balance"] - state["reward_issuance_balance"]
    ) 


def earned_minus_burned_supply(state: SubspaceModelState) -> Credits:
    return earned_supply(state) - state["burnt_balance"]


def total_supply(state: SubspaceModelState) -> Credits:
    return issued_supply(state) - state["burnt_balance"]


def sum_of_stocks(state: SubspaceModelState) -> Credits:
    return (
        earned_supply(state)
        + state["vesting_balance"]
        + state["reward_issuance_balance"]
        + state["burnt_balance"]
    )


def storage_fee_per_rewards(state: SubspaceModelState) -> Credits:
    return state["storage_fee_volume"] / max(1, state["block_reward"])

def community_vested_supply(state: SubspaceModelState, params: SubspaceModelParams) -> Credits:
    return state['allocated_tokens_testnets'] + state['allocated_tokens_foundation'] + state['allocated_tokens_ambassadors']

def community_owned_supply(state: SubspaceModelState, params: SubspaceModelParams) -> Credits:
    return state['cumm_rewards'] + community_vested_supply(state, params)


def community_owned_supply_fraction(state: SubspaceModelState, params: SubspaceModelParams):
    return community_owned_supply(state, params) / total_supply(state)
