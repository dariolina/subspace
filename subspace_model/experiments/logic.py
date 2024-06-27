import random
from typing import Callable, List, Any
import numpy as np
from scipy.stats import norm, poisson  # type: ignore
from cadCAD.tools.preparation import sweep_cartesian_product  # type: ignore
from subspace_model.const import (
    BLOCKS_PER_MONTH,
    BLOCKS_PER_YEAR,
    DAY_TO_SECONDS,
    ISSUANCE_FOR_FARMERS
)
from subspace_model.metrics import (
    earned_minus_burned_supply,
    earned_supply,
    issued_supply,
    total_supply,
    circulating_supply
)
from subspace_model.types import (
    StochasticFunction,
    SubspaceModelParams,
    SubspaceModelState,
    SubsidyComponent,
)


def DEFAULT_SLASH_FUNCTION(params: SubspaceModelParams, state: SubspaceModelState):
    return state["staking_pool_balance"] * 0  # HACK


def NORMAL_GENERATOR(mu: float, sigma: float) -> StochasticFunction:
    np.random.seed()
    return lambda p, s: norm.rvs(mu, sigma, random_state=np.random.RandomState())


def NORMAL_INSTANTANEOUS_SHOCK_GENERATOR(
    mu: float, sigma: float, N: int
) -> StochasticFunction:
    np.random.seed()

    def generator(p, s):
        value = norm.rvs(mu, sigma, random_state=np.random.RandomState())
        if s["days_passed"] % (N * 7) == 0:
            if np.random.choice([0, 1]):
                value *= 10
            else:
                value /= 10
        return value

    return generator


def NORMAL_SUSTAINED_SHOCK_GENERATOR(
    mu: float, sigma: float, N: int, M: int
) -> StochasticFunction:
    np.random.seed()

    def generator(p, s):
        value = norm.rvs(mu, sigma, random_state=np.random.RandomState())
        if s["days_passed"] % (N * 7) < M:
            if (N * 7) % 2:
                value *= 10
            else:
                value /= 10
        return value

    return generator


def POISSON_GENERATOR(mu: float) -> StochasticFunction:
    np.random.seed()
    return lambda p, s: poisson.rvs(mu, random_state=np.random.RandomState())


def POSITIVE_INTEGER(generator: StochasticFunction) -> StochasticFunction:
    return lambda p, s: max(0, int(generator(p, s)))


def MAGNITUDE(generator: StochasticFunction) -> StochasticFunction:
    return lambda p, s: min(1, max(0, generator(p, s)))


def predictable_trajectory(mean: float, **params: Any) -> Callable:
    mu: float = mean
    sigma: float = 0.3 * mu
    generator: Callable = NORMAL_GENERATOR(mu, sigma)
    return generator


def high_volatility_trajectory(mean: float, **params: Any) -> Callable:
    mu: float = mean
    sigma: float = 5 * mu
    generator: Callable = NORMAL_GENERATOR(mu, sigma)
    return generator


def predictable_trajectory_with_instantaneous_shocks(
    mean: float, **params: Any
) -> Callable:
    mu: float = mean
    sigma: float = 0.3 * mu
    generator: Callable = NORMAL_INSTANTANEOUS_SHOCK_GENERATOR(
        mu, sigma, N=params.get("N", 13)
    )
    return generator


def predictable_trajectory_with_sustained_shocks(
    mean: float, **params: Any
) -> Callable:
    mu: float = mean
    sigma: float = 0.3 * mu
    generator: Callable = NORMAL_SUSTAINED_SHOCK_GENERATOR(
        mu, sigma, N=params.get("N", 13), M=params.get("M", 7)
    )
    return generator


def SCENARIO_GROUPS(means: List[float], N: int = 13, M: int = 7) -> List[Callable]:
    # Subsample battery to conserve cardinality of scenarios parameter space
    groups: List[Callable] = random.sample(
        [
            predictable_trajectory,
            high_volatility_trajectory,
            predictable_trajectory_with_instantaneous_shocks,
            predictable_trajectory_with_sustained_shocks,
        ],
        1,  # XXX This value can range from 1 to 4 to scale up the cardinality of scenarios
    )
    results: List[Callable] = []
    for mean in means:
        if mean != 0:
            for group in groups:
                results.append(group(mean))
        else:
            results.append(lambda p, s: 0)
    return results


SUPPLY_ISSUED = issued_supply

SUPPLY_EARNED = earned_supply

SUPPLY_EARNED_MINUS_BURNED = earned_minus_burned_supply

CIRCULATING_SUPPLY = circulating_supply

SUPPLY_TOTAL = total_supply


REFERENCE_SUBSIDY_CONSTANT_SINGLE_COMPONENT = [
    SubsidyComponent(0, 2 * BLOCKS_PER_YEAR, 10_000,
                     10_000 / (2 * BLOCKS_PER_YEAR)),
]
REFERENCE_SUBSIDY_HYBRID_SINGLE_COMPONENT = [
    SubsidyComponent(0, BLOCKS_PER_MONTH, 10_000, 1_000 / BLOCKS_PER_MONTH),
]
REFERENCE_SUBSIDY_HYBRID_TWO_COMPONENTS = [
    SubsidyComponent(0, BLOCKS_PER_MONTH, 5_000, 1_000 / BLOCKS_PER_MONTH),
    SubsidyComponent(
        6 * BLOCKS_PER_MONTH, 7 * BLOCKS_PER_MONTH, 5_000, 1_000 / BLOCKS_PER_MONTH
    ),
]
REFERENCE_SUBSIDY_MAINNET_TWO_COMPONENTS = [
    SubsidyComponent(7, 0, 0.5 * ISSUANCE_FOR_FARMERS, 0.25),
    SubsidyComponent(
        7, 365.25*2, 0.5 * ISSUANCE_FOR_FARMERS, 0.25),
]

def MAINNET_REFERENCE_SUBSIDY_COMPONENTS():
    component_1_start_days = [7]
    component_2_start_days = [7]

    component_1_initial_subsidy_duration = [0]
    component_1_initial_subsidies = [2.5]
    component_1_maximum_cumulative_subsidies = [
        0.5 * ISSUANCE_FOR_FARMERS]

    component_2_initial_subsidy_duration = [
        24 * (365.25 / 12),
    ]
    component_2_initial_subsidies = [2.5]
    component_2_maximum_cumulative_subsidies = [
                                            0.5 * ISSUANCE_FOR_FARMERS]

    cartesian_product = sweep_cartesian_product(
        {
            "component_1_start_days": component_1_start_days,
            "component_1_initial_subsidy_duration": component_1_initial_subsidy_duration,
            "component_1_initial_subsidies": component_1_initial_subsidies,
            "component_1_maximum_cumulative_subsidies": component_1_maximum_cumulative_subsidies,
            "component_2_start_days": component_2_start_days,
            "component_2_initial_subsidy_duration": component_2_initial_subsidy_duration,
            "component_2_initial_subsidies": component_2_initial_subsidies,
            "component_2_maximum_cumulative_subsidies": component_2_maximum_cumulative_subsidies,
        }  # type: ignore
    )

    components = [
        (
            SubsidyComponent(
                start1,
                duration1,
                maximum_cumulative_subsidy1,
                initial_subsidy1,
            ),
            SubsidyComponent(
                start2,
                duration2,
                maximum_cumulative_subsidy2,
                initial_subsidy2,)
        )
        for start1, duration1, initial_subsidy1, maximum_cumulative_subsidy1, start2, duration2, initial_subsidy2, maximum_cumulative_subsidy2 in zip(
            cartesian_product['component_1_start_days'],
            cartesian_product['component_1_initial_subsidy_duration'],
            cartesian_product['component_1_initial_subsidies'],
            cartesian_product['component_1_maximum_cumulative_subsidies'],
            cartesian_product['component_2_start_days'],
            cartesian_product['component_2_initial_subsidy_duration'],
            cartesian_product['component_2_initial_subsidies'],
            cartesian_product['component_2_maximum_cumulative_subsidies'],
        )]

    return components



DEFAULT_REFERENCE_SUBSIDY_COMPONENTS = MAINNET_REFERENCE_SUBSIDY_COMPONENTS()[
    -1]


def TRANSACTION_COUNT_PER_DAY_FUNCTION_CONSTANT_UTILIZATION_50(
    params: SubspaceModelParams, state: SubspaceModelState
) -> float:
    average_transaction_size = state["average_transaction_size"]
    max_size = (
        params["max_block_size"] * DAY_TO_SECONDS *
        params["block_time_in_seconds"]
    )

    # Hold a constant utilization rate of 0.5
    transaction_count = 0.5 * max_size / average_transaction_size

    return transaction_count


def TRANSACTION_COUNT_PER_DAY_FUNCTION_GROWING_UTILIZATION_TWO_YEARS(
    params: SubspaceModelParams, state: SubspaceModelState
) -> float:

    days_passed = state["days_passed"]
    average_transaction_size = state["average_transaction_size"]
    max_size = (
        params["max_block_size"] * DAY_TO_SECONDS *
        params["block_time_in_seconds"]
    )

    utilization = min(days_passed / (2 * 365), 1)

    # Grow utilization rate from 0 to 1 over 2 years
    transaction_count = utilization * max_size / average_transaction_size

    return transaction_count


def TRANSACTION_COUNT_PER_DAY_FUNCTION_FROM_UTILIZATION_RATIOS(
    params: SubspaceModelParams, state: SubspaceModelState
) -> float:
    max_size = (
        params["max_block_size"] * DAY_TO_SECONDS *
        params["block_time_in_seconds"]
    )
    transaction_volume = max_size * state["block_utilization"]
    transaction_count = transaction_volume / state["average_transaction_size"]
    return transaction_count


def WEEKLY_VARYING(params: SubspaceModelParams, state: SubspaceModelState):
    return 2 + np.sin(2 * np.pi * state["days_passed"] / 7)
