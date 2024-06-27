import pandas as pd
import pytest as pt

from subspace_model.experiments.experiment import psuu
from subspace_model.psuu import timestep_tensor_to_trajectory_tensor
from subspace_model.const import MAX_CREDIT_ISSUANCE, ISSUANCE_FOR_FARMERS

@pt.fixture(scope="module", params=[(100, 50, 1), (1000, 2, 1)])
def sim_df(request) -> pd.DataFrame:
    (SIMULATION_DAYS, N_SWEEP_SAMPLES, SAMPLES) = request.param
    return psuu(SIMULATION_DAYS=SIMULATION_DAYS,
                TIMESTEP_IN_DAYS=1,
                SAMPLES=SAMPLES,
                N_SWEEP_SAMPLES=N_SWEEP_SAMPLES,
                SWEEPS_PER_PROCESS=1,
                PROCESSES=1,
                PARALLELIZE=False,
                USE_JOBLIB=False,
                RETURN_SIM_DF=True)


def test_run(sim_df):
    df = sim_df.query('timestep > 0')
    assert df.isnull().sum().sum() == 0


def test_kpi_values(sim_df):
    agg_df = timestep_tensor_to_trajectory_tensor(sim_df)

    # Per-Trajectory Co-Domain Tests
    for i, row in agg_df.iterrows():
        assert row['mean_relative_community_owned_supply'] > 0.01
        assert row['mean_relative_community_owned_supply'] < 1.0
        assert row['mean_farmer_subsidy_factor'] > 0
        assert row['mean_proposing_rewards_per_newly_pledged_space'] > 0
        assert row['mean_proposer_reward_minus_voter_reward'] > 0
        assert row['cumm_rewards_before_1yr'] > 0
        assert row['abs_sum_storage_fees_per_sum_compute_fees'] > 0
        assert row['cumm_rewards'] >= row['cumm_rewards_before_1yr']

    # Aggregate Co-Domain Tests
    assert agg_df['mean_relative_community_owned_supply'].mean() > 0.01
    assert agg_df['mean_relative_community_owned_supply'].mean() < 1.0
    assert agg_df['mean_farmer_subsidy_factor'].mean() > 0
    assert agg_df['mean_proposing_rewards_per_newly_pledged_space'].mean() > 0
    assert agg_df['mean_proposer_reward_minus_voter_reward'].mean() > 0
    assert agg_df['cumm_rewards_before_1yr'].mean() > 0
    assert agg_df['abs_sum_storage_fees_per_sum_compute_fees'].mean() > 0
    assert agg_df['cumm_rewards'].mean(
    ) >= agg_df['cumm_rewards_before_1yr'].mean()


def test_state_variables(sim_df):
    for i_traj, df in sim_df.groupby(['simulation', 'subset', 'run']):
        for i_row, row in df.iterrows():
            assert row['allocated_tokens'] == pt.approx(MAX_CREDIT_ISSUANCE - ISSUANCE_FOR_FARMERS - 
                                                        (row['allocated_tokens_investors']
                                                        + row['allocated_tokens_founders']
                                                        + row['allocated_tokens_team']
                                                        + row['allocated_tokens_advisors']
                                                        + row['allocated_tokens_vendors']
                                                        + row['allocated_tokens_ambassadors']
                                                        + (row['allocated_tokens_foundation'] - 0.07 * MAX_CREDIT_ISSUANCE)
                                                        + row['allocated_tokens_ssl_priv_sale']
                                                        + (row['allocated_tokens_subspace_labs'] - 0.02 * MAX_CREDIT_ISSUANCE)))
            
            assert row['sum_of_stocks'] == pt.approx(MAX_CREDIT_ISSUANCE)
            assert row['circulating_supply'] <= row['sum_of_stocks']
            assert row['total_supply'] <= row['sum_of_stocks']
            assert row['user_supply'] <= row['sum_of_stocks']
            assert row['issued_supply'] <= row['sum_of_stocks']
            assert row['earned_supply'] <= row['sum_of_stocks']
            assert row['earned_minus_burned_supply'] <= row['sum_of_stocks']
            assert row['community_owned_supply'] <= row['sum_of_stocks']

            assert row['farmers_balance'] >= 0.0
            assert row['nominators_balance'] >= 0.0
            assert row['operators_balance'] >= 0.0

            assert row['circulating_supply'] >= 0.0
            assert row['total_supply'] >= 0.0
            assert row['user_supply'] >= 0.0
            assert row['issued_supply'] >= 0.0
            assert row['earned_supply'] >= 0.0
            assert row['earned_minus_burned_supply'] >= 0.0
            assert row['community_owned_supply'] >= 0.0

            assert row['nominator_pool_shares'] >= 0.0
            assert row['operator_pool_shares'] >= 0.0

            assert row['circulating_supply'] <= row['user_supply']
            assert row['earned_minus_burned_supply'] <= row['earned_supply']


        assert df.sum_of_stocks.std() == pt.approx(0.0, abs=1e-4)
        assert df.sum_of_stocks.max() == pt.approx(MAX_CREDIT_ISSUANCE)
                

