from typing import Callable, TypedDict, get_origin, Union, get_args
import math
from dataclasses import dataclass
import pandera as pa

from subspace_model.units import *
from subspace_model.const import BLOCKS_PER_DAY
@dataclass
class SubsidyComponent:
    initial_period_start: Days  # τ_{0, i}
    initial_period_duration: Days  # τ_{1, i}
    max_cumulative_subsidy: Credits  # Ω_i. The max that can be disbursed globally
    max_reference_subsidy: CreditsPerBlock  # α_i. The max that can be disbursed per block


    @property
    def initial_period_start_in_blocks(self) -> Blocks:
        return self.initial_period_start * BLOCKS_PER_DAY
    
    @property
    def initial_period_duration_in_blocks(self) -> Blocks:
        return self.initial_period_duration * BLOCKS_PER_DAY
    
    @property
    def initial_period_end_duration_in_blocks(self) -> Blocks:
        return (self.initial_period_start + self.initial_period_end) * BLOCKS_PER_DAY
    
    # Dataclass constructor method
    def __post_init__(self):
        self.initial_period_end = self.initial_period_start + self.initial_period_duration

    def __call__(self, t: Blocks) -> float:
        """Allow the instance to be called as a function to calculate the subsidy."""
        return self.calculate_subsidy(t)

    def calculate_subsidy(self, t: Blocks) -> CreditsPerBlock:
        """Calculate S(t) the subsidy for a given time."""
        if t < self.initial_period_start_in_blocks:
            return 0.0
        elif t < self.initial_period_end_duration_in_blocks:
            return self.calculate_linear_subsidy(t)
        else:
            return self.calculate_exponential_subsidy(t)

    def calculate_linear_subsidy(self, t: Days) -> CreditsPerBlock:
        """Calculate S_l(t) the linear subsidy for a given time."""
        return self.max_reference_subsidy

    def calculate_exponential_subsidy(self, t: float) -> CreditsPerBlock:
        """Calculate S_e(t) the exponential subsidy for a given time."""
        K = self.max_total_subsidy_during_exponential_period
        if K > 0:
            return self.max_reference_subsidy * math.exp(
                -self.max_reference_subsidy / max(1, K * (t - self.initial_period_end_duration_in_blocks))
            )
        else:
            return 0

    @property
    def max_total_subsidy_during_exponential_period(self) -> Credits:
        """Calculate K the maximum total subsidy during the exponential period."""
        return self.max_cumulative_subsidy - self.max_reference_subsidy * (
            self.initial_period_end_duration_in_blocks - self.initial_period_start_in_blocks
        )

    @property
    def halving_period(self) -> Blocks:
        """Calculate L the halving period for the component rewards."""
        K = self.max_total_subsidy_during_exponential_period
        return K * math.log(2) / self.max_reference_subsidy




class SubspaceModelState(TypedDict):
    # Time Variables
    timestep: int
    substep: int
    days_passed: Days
    delta_days: Days
    blocks_passed: Blocks
    delta_blocks: Blocks

    # Metrics
    # Supply Related
    circulating_supply: Credits
    user_supply: Credits
    issued_supply: Credits
    sum_of_stocks: Credits
    earned_supply: Credits
    earned_minus_burned_supply: Credits
    total_supply: Credits
    community_owned_supply: Credits

    # Network Related
    block_utilization: Percentage
    compute_fee_volume: Credits
    storage_fee_volume: Credits

    # Reward Related
    per_recipient_reward: Credits
    proposer_bonus_reward: Credits
    reward_to_proposer: Credits
    reward_to_voters: Credits

    # Governance Variables
    dsf_relative_disbursal_per_day: Percentage

    # Stocks
    reward_issuance_balance: Credits
    vesting_balance: Credits
    operators_balance: Credits
    nominators_balance: Credits
    farmers_balance: Credits
    staking_pool_balance: Credits
    burnt_balance: Credits

    # Staking Pool Shares
    nominator_pool_shares: float
    operator_pool_shares: float

    # Deterministic Variables
    block_reward: Credits
    blockchain_history_size: Bytes
    total_space_pledged: Bytes
    buffer_size: Bytes


    # Token Vesting
    allocated_tokens: Credits
    allocated_tokens_investors: Credits
    allocated_tokens_founders: Credits
    allocated_tokens_team: Credits
    allocated_tokens_advisors: Credits
    allocated_tokens_vendors: Credits
    allocated_tokens_ambassadors: Credits
    allocated_tokens_testnets: Credits
    allocated_tokens_foundation: Credits
    allocated_tokens_subspace_labs: Credits
    allocated_tokens_ssl_priv_sale: Credits
    # Environmental Variables

    # Fee Related
    average_priority_fee: ShannonPerComputeWeights

    # Tx Related
    average_compute_weight_per_tx: ComputeWeights
    average_transaction_size: Bytes
    transaction_count: int
    average_compute_weight_per_bundle: ComputeWeights
    average_bundle_size: Bytes
    bundle_count: int

    # Uncategorized Terms
    storage_fee_per_rewards: float
    reference_subsidy: CreditsPerBlock
    compute_fee_multiplier: float
    replication_factor: float
    extrinsic_length_in_bytes: float
    storage_fee_in_shannon_per_bytes: float
    priority_fee_volume: float
    consensus_extrinsic_fee_volume: float
    max_normal_weight: float
    max_bundle_weight: float
    target_block_fullness: float
    adjustment_variable: float
    target_block_delta: float
    targeted_adjustment_parameter: float
    tx_compute_weight: float


    ## Cummulative Metrics
    cumm_rewards: Credits 
    cumm_storage_fees_to_farmers: Credits 
    cumm_compute_fees_to_farmers: Credits 


class SubspaceModelParams(TypedDict):
    # Meta
    label: str
    environmental_label: str
    timestep_in_days: Days

    # Mechanism Parameters
    slash_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], Credits]
    reference_subsidy_components: list[SubsidyComponent]
    utilization_ratio_smooth_num_blocks: int

    # Implementation parameters
    block_time_in_seconds: Seconds
    archival_depth: Blocks
    archival_buffer_segment_size: Bytes
    header_size: Bytes
    min_replication_factor: float
    max_block_size: Bytes
    weight_to_fee: Credits

    # Economic Parameters
    reward_recipients: int
    reward_proposer_share: Percentage
    max_credit_supply: Credits
    credit_supply_definition: Callable[[SubspaceModelState], Credits]

    # Fees & Taxes
    compute_fees_to_farmers: Percentage
    compute_fees_tax_to_operators: Percentage

    # Slash Parameters
    slash_to_farmers: Percentage

    # Other
    initial_community_owned_supply_pct_of_max_credits: Percentage

    # Behavioral Parameters
    operator_stake_per_ts_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], Percentage]
    nominator_stake_per_ts_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], Percentage]
    transfer_operator_to_farmer_per_day_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], Percentage]
    transfer_farmer_to_nominator_per_day_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], Percentage]
    transfer_farmer_to_operator_per_day_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], Percentage]

    # Environmental Parameters
    # Environmental: Fees
    # base_fee_function: Callable[[bool], Percentage]
    # min_base_fee: Credits
    priority_fee_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], Percentage]

    # Enviromental: Compute Weights per Tx
    compute_weights_per_tx_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], ComputeWeights]
    min_compute_weights_per_tx: ComputeWeights
    compute_weight_per_bundle_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], ComputeWeights]
    min_compute_weights_per_bundle: ComputeWeights

    # Environmental: Tx Sizes
    transaction_size_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], Bytes]
    min_transaction_size: Bytes
    bundle_size_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], Bytes]
    min_bundle_size: Bytes  # XXX

    # Environmental: Tx Count
    transaction_count_per_day_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], float]
    bundle_count_per_day_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], float]

    # Environmental: Slash Count
    slash_per_day_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], float]

    # Environmental: Space Pledged per Time
    newly_pledged_space_per_day_function: Callable[[
        'SubspaceModelParams', SubspaceModelState], Bytes]
    utilization_ratio: Percentage
    
    # Other
    utilization_ratio_function: Callable[['SubspaceModelParams', SubspaceModelState], Callable]

# Logic implementation types
StochasticFunction = Callable[[SubspaceModelParams, SubspaceModelState], float]


raw_state_type_hints = {k: v for k,
                        v in SubspaceModelState.__annotations__.items()}


state_type_hints = {k: v if get_origin(v) != Union
                    else get_args(v)[0]
                    for k, v in raw_state_type_hints.items()}

state_tensor_type_hints = {'simulation': int,
                           'subset': int,
                           'run': int,
                           'timestep': int,
                           'substep': int,
                           **state_type_hints}

state_tensor_type_hints_as_cols = {
    k: pa.Column(v) for k, v in state_tensor_type_hints.items()}

TimestepStateTensor = pa.DataFrameSchema(state_tensor_type_hints_as_cols)

per_traj_state_tensor_type_hints_as_cols = state_tensor_type_hints_as_cols.copy()

per_traj_state_tensor_type_hints_as_cols.pop('simulation')
per_traj_state_tensor_type_hints_as_cols.pop('subset')
per_traj_state_tensor_type_hints_as_cols.pop('run')

PerTrajectoryTimestepStateTensor = pa.DataFrameSchema(per_traj_state_tensor_type_hints_as_cols)

