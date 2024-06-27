from copy import deepcopy

import numpy as np
import pandas as pd
from cadCAD.tools import easy_run  # type: ignore
from cadCAD.tools.preparation import sweep_cartesian_product  # type: ignore
from pandas import DataFrame
from random import sample
from datetime import datetime
from joblib import Parallel, delayed  # type: ignore
from glob import glob
import re
from tqdm.auto import tqdm # type: ignore
import logging
from pathlib import Path
import os
from multiprocessing import cpu_count
from subspace_model.psuu import timestep_tensor_to_trajectory_tensor
import boto3 # type: ignore

logger = logging.getLogger('subspace-digital-twin')
CLOUD_BUCKET_NAME = 'subspace-simulations'


from subspace_model.const import *
from subspace_model.experiments.logic import (
    REFERENCE_SUBSIDY_CONSTANT_SINGLE_COMPONENT,
    REFERENCE_SUBSIDY_HYBRID_SINGLE_COMPONENT,
    REFERENCE_SUBSIDY_HYBRID_TWO_COMPONENTS,
    SUPPLY_EARNED,
    SUPPLY_EARNED_MINUS_BURNED,
    SUPPLY_ISSUED,
    CIRCULATING_SUPPLY,
    TRANSACTION_COUNT_PER_DAY_FUNCTION_CONSTANT_UTILIZATION_50,
    TRANSACTION_COUNT_PER_DAY_FUNCTION_GROWING_UTILIZATION_TWO_YEARS,
)
from subspace_model.params import (
    DEFAULT_PARAMS,
    ENVIRONMENTAL_SCENARIOS,
    SPECIAL_ENVIRONMENTAL_SCENARIOS,
    GOVERNANCE_SURFACE,
)
from subspace_model.state import INITIAL_STATE
from subspace_model.structure import SUBSPACE_MODEL_BLOCKS


def sanity_check_run(
    SIMULATION_DAYS: int = 183, TIMESTEP_IN_DAYS: int = 1, SAMPLES: int = 1, **kwargs
) -> DataFrame:
    """
    This experiment tests the model with default parameters and with deterministic parameters.

    Returns:
        DataFrame: A dataframe of simulation data
    """
    TIMESTEPS = int(SIMULATION_DAYS / TIMESTEP_IN_DAYS) + 1

    # Get the sweep params in the form of single length arrays
    sweep_params = {k: [v] for k, v in DEFAULT_PARAMS.items()}

    # Load simulation arguments
    sim_args = (INITIAL_STATE, sweep_params, SUBSPACE_MODEL_BLOCKS, TIMESTEPS, SAMPLES)

    # Run simulation
    sim_df = easy_run(
        *sim_args,
        assign_params={
            "label",
            "environmental_label",
            "timestep_in_days",
            "block_time_in_seconds",
            "max_credit_supply",
        },
        exec_mode="single",
        deepcopy_off=True,
        supress_print=True
    )
    return sim_df


def standard_stochastic_run(
    SIMULATION_DAYS: int = 183, TIMESTEP_IN_DAYS: int = 1, SAMPLES: int = 5, **kwargs
) -> DataFrame:
    """Function which runs the cadCAD simulations

    Returns:
        DataFrame: A dataframe of simulation data
    """
    TIMESTEPS = int(SIMULATION_DAYS / TIMESTEP_IN_DAYS) + 1

    # Get the sweep parameters in the form of single length arrays
    param_set = deepcopy(DEFAULT_PARAMS)

    sweep_params = {
        **{k: [v] for k, v in param_set.items()},
        **{k: [v] for k, v in SPECIAL_ENVIRONMENTAL_SCENARIOS["stochastic"].items()},
    }

    # Load simulation arguments
    sim_args = (INITIAL_STATE, sweep_params, SUBSPACE_MODEL_BLOCKS, TIMESTEPS, SAMPLES)

    # Run simulation
    sim_df = easy_run(
        *sim_args,
        assign_params={
            "label",
            "environmental_label",
            "timestep_in_days",
            "block_time_in_seconds",
            "max_credit_supply",
        },
        exec_mode="single",
        deepcopy_off=True,
        supress_print=True
    )
    return sim_df


def reward_split_sweep(
    SIMULATION_DAYS: int = 183,
    TIMESTEP_IN_DAYS: int = 1,
    SAMPLES: int = 1,
) -> DataFrame:
    """Function which runs the cadCAD simulations

    Returns:
        DataFrame: A dataframe of simulation data
    """
    TIMESTEPS = int(SIMULATION_DAYS / TIMESTEP_IN_DAYS) + 1

    # Get the sweep params in the form of single length arrays
    param_set_1 = DEFAULT_PARAMS
    param_set_2 = deepcopy(DEFAULT_PARAMS)
    param_set_2["label"] = "alternate-split"
    param_set_2["reward_proposer_share"] = 0.5

    param_sets = [param_set_1, param_set_2]

    sweep_params: dict[str, list] = {k: [] for k in DEFAULT_PARAMS.keys()}
    for param_set in param_sets:
        for k, v in param_set.items():
            sweep_params[k].append(v)

    # Load simulation arguments
    sim_args = (INITIAL_STATE, sweep_params, SUBSPACE_MODEL_BLOCKS, TIMESTEPS, SAMPLES)

    # Run simulation
    sim_df = easy_run(
        *sim_args,
        assign_params={
            "label",
            "environmental_label",
            "timestep_in_days",
            "block_time_in_seconds",
            "max_credit_supply",
        },
        exec_mode="single",
        deepcopy_off=True,
        supress_print=True
    )
    return sim_df


def sweep_credit_supply(
    SIMULATION_DAYS: int = 183,
    TIMESTEP_IN_DAYS: int = 1,
    SAMPLES: int = 1,
    **kwargs
) -> DataFrame:
    """ """
    TIMESTEPS = int(SIMULATION_DAYS / TIMESTEP_IN_DAYS) + 1

    # Get the sweep params in the form of single length arrays
    param_set_1 = deepcopy(DEFAULT_PARAMS)
    param_set_1["label"] = "supply-issued"
    param_set_1["credit_supply_definition"] = SUPPLY_ISSUED
    param_set_1["environmental_label"] = "constant-utilization"
    param_set_1["transaction_count_per_day_function"] = (
        TRANSACTION_COUNT_PER_DAY_FUNCTION_CONSTANT_UTILIZATION_50
    )

    # param_set_2 = deepcopy(DEFAULT_PARAMS)
    # param_set_2["label"] = "supply-earned"
    # param_set_2["credit_supply_definition"] = SUPPLY_EARNED
    # param_set_2["environmental_label"] = "constant-utilization"
    # param_set_2["transaction_count_per_day_function"] = (
    #     TRANSACTION_COUNT_PER_DAY_FUNCTION_CONSTANT_UTILIZATION_50
    # )

    # param_set_3 = deepcopy(DEFAULT_PARAMS)
    # param_set_3["label"] = "supply-earned-minus-burned"
    # param_set_3["credit_supply_definition"] = SUPPLY_EARNED_MINUS_BURNED
    # param_set_3["environmental_label"] = "constant-utilization"
    # param_set_3["transaction_count_per_day_function"] = (
    #     TRANSACTION_COUNT_PER_DAY_FUNCTION_CONSTANT_UTILIZATION_50
    #)

    param_set_4 = deepcopy(DEFAULT_PARAMS)
    param_set_4["label"] = "supply-issued"
    param_set_4["credit_supply_definition"] = SUPPLY_ISSUED
    param_set_4["environmental_label"] = "growing-utilization"
    param_set_4["transaction_count_per_day_function"] = (
        TRANSACTION_COUNT_PER_DAY_FUNCTION_GROWING_UTILIZATION_TWO_YEARS
    )

    # param_set_5 = deepcopy(DEFAULT_PARAMS)
    # param_set_5["label"] = "supply-earned"
    # param_set_5["credit_supply_definition"] = SUPPLY_EARNED
    # param_set_5["environmental_label"] = "growing-utilization"
    # param_set_5["transaction_count_per_day_function"] = (
    #     TRANSACTION_COUNT_PER_DAY_FUNCTION_GROWING_UTILIZATION_TWO_YEARS
    # )

    # param_set_6 = deepcopy(DEFAULT_PARAMS)
    # param_set_6["label"] = "supply-earned-minus-burned"
    # param_set_6["credit_supply_definition"] = SUPPLY_EARNED_MINUS_BURNED
    # param_set_6["environmental_label"] = "growing-utilization"
    # param_set_6["transaction_count_per_day_function"] = (
    #     TRANSACTION_COUNT_PER_DAY_FUNCTION_GROWING_UTILIZATION_TWO_YEARS
    # )
    param_set_7 = deepcopy(DEFAULT_PARAMS)
    param_set_7["label"] = "circulating-supply"
    param_set_7["credit_supply_definition"] = CIRCULATING_SUPPLY
    param_set_7["environmental_label"] = "constant-utilization"
    param_set_7["transaction_count_per_day_function"] = (
        TRANSACTION_COUNT_PER_DAY_FUNCTION_CONSTANT_UTILIZATION_50
    )

    param_set_8 = deepcopy(DEFAULT_PARAMS)
    param_set_8["label"] = "circulating-supply"
    param_set_8["credit_supply_definition"] = CIRCULATING_SUPPLY
    param_set_8["environmental_label"] = "growing-utilization"
    param_set_8["transaction_count_per_day_function"] = (
        TRANSACTION_COUNT_PER_DAY_FUNCTION_GROWING_UTILIZATION_TWO_YEARS
    )

    param_sets = [
        param_set_1,
        #param_set_2,
        # param_set_3,
        param_set_4,
        #param_set_5,
        #param_set_6,
        param_set_7,
        param_set_8
    ]

    sweep_params: dict[str, list] = {k: [] for k in DEFAULT_PARAMS.keys()}
    for param_set in param_sets:
        for k, v in param_set.items():
            sweep_params[k].append(v)

    # Load simulation arguments
    sim_args = (INITIAL_STATE, sweep_params, SUBSPACE_MODEL_BLOCKS, TIMESTEPS, SAMPLES)

    # Run simulation
    sim_df = easy_run(
        *sim_args,
        assign_params={
            "label",
            "environmental_label",
            "timestep_in_days",
            "block_time_in_seconds",
            "max_credit_supply",
        },
        exec_mode="single",
        deepcopy_off=True,
        supress_print=True
    )
    return sim_df


def initial_conditions(
    SIMULATION_DAYS: int = 183, TIMESTEP_IN_DAYS: int = 1, SAMPLES: int = 30, **kwargs
) -> DataFrame:
    """Function which runs the cadCAD simulations

    Returns:
        DataFrame: A dataframe of simulation data
    """
    TIMESTEPS = int(SIMULATION_DAYS / TIMESTEP_IN_DAYS) + 1

    # Get the sweep parameters in the form of single length arrays
    param_set = deepcopy(DEFAULT_PARAMS)

    sweep_params = {
        **{k: [v] for k, v in param_set.items()},
        **{k: [v] for k, v in SPECIAL_ENVIRONMENTAL_SCENARIOS["stochastic"].items()},
    }

    # Load simulation arguments
    sim_args = (INITIAL_STATE, sweep_params, SUBSPACE_MODEL_BLOCKS, TIMESTEPS, SAMPLES)

    # Run simulation
    sim_df = easy_run(
        *sim_args,
        assign_params={
            "label",
            "environmental_label",
            "timestep_in_days",
            "block_time_in_seconds",
            "max_credit_supply",
        },
        exec_mode="single",
        deepcopy_off=True,
        supress_print=True
    )
    return sim_df


def reference_subsidy_sweep(
    SIMULATION_DAYS: int = 360, TIMESTEP_IN_DAYS: int = 1, SAMPLES: int = 1
) -> DataFrame:
    """Sweeps issuance functions.

    Returns:
        DataFrame: A dataframe of simulation data
    """

    TIMESTEPS = int(SIMULATION_DAYS / TIMESTEP_IN_DAYS) + 1

    # Get the sweep params in the form of single length arrays
    param_set_1 = deepcopy(DEFAULT_PARAMS)
    param_set_1["label"] = "constant-single-component"
    param_set_1["reference_subsidy_components"] = (
        REFERENCE_SUBSIDY_CONSTANT_SINGLE_COMPONENT
    )

    param_set_2 = deepcopy(DEFAULT_PARAMS)
    param_set_2["label"] = "hybrid-single-component"
    param_set_2["reference_subsidy_components"] = (
        REFERENCE_SUBSIDY_HYBRID_SINGLE_COMPONENT
    )

    param_set_3 = deepcopy(DEFAULT_PARAMS)
    param_set_3["label"] = "hybrid-two-components"
    param_set_3["reference_subsidy_components"] = (
        REFERENCE_SUBSIDY_HYBRID_TWO_COMPONENTS
    )
    param_sets = [param_set_1, param_set_2, param_set_3]

    sweep_params: dict[str, list] = {k: [] for k in DEFAULT_PARAMS.keys()}
    for param_set in param_sets:
        for k, v in param_set.items():
            sweep_params[k].append(v)

    # Load simulation arguments
    sim_args = (INITIAL_STATE, sweep_params, SUBSPACE_MODEL_BLOCKS, TIMESTEPS, SAMPLES)

    # Run simulation
    sim_df = easy_run(
        *sim_args,
        assign_params={
            "label",
            "environmental_label",
            "timestep_in_days",
            "block_time_in_seconds",
            "max_credit_supply",
        },
        exec_mode="single",
        deepcopy_off=True,
        supress_print=True
    )
    return sim_df


def psuu(
    SIMULATION_DAYS: int = 3 * 365,
    TIMESTEP_IN_DAYS: int = 1,
    SAMPLES: int = 2,
    N_SWEEP_SAMPLES: int = 48,
    SWEEPS_PER_PROCESS: int = 20,
    PROCESSES: int = cpu_count(),
    PARALLELIZE: bool = True,
    USE_JOBLIB: bool = True,
    RETURN_SIM_DF: bool = False,
    UPLOAD_TO_S3: bool = False,
):
    """Function which runs the cadCAD simulations

    Returns:
        DataFrame: A dataframe of simulation data
    """

    invoke_time = datetime.now()
    logger.info(f"PSuU Exploratory Run invoked at {invoke_time}")

    TIMESTEPS = int(SIMULATION_DAYS / TIMESTEP_IN_DAYS) + 1

    default_params = deepcopy(DEFAULT_PARAMS)

    sweep_params = sweep_cartesian_product(
        {
            **{k: [v] for k, v in default_params.items()},
            **ENVIRONMENTAL_SCENARIOS,
            **GOVERNANCE_SURFACE,
        }
    )

    # Sample the sweep space
    sweep_params_samples = {
        k: sample(v, N_SWEEP_SAMPLES) if N_SWEEP_SAMPLES > 0 else v
        for k, v in sweep_params.items()
    }

    # Load simulation arguments
    sim_args = (
        INITIAL_STATE,
        sweep_params_samples,
        SUBSPACE_MODEL_BLOCKS,
        TIMESTEPS,
        SAMPLES,
    )
    assign_params = {
        "label",
        "environmental_label",
        "timestep_in_days",
        "block_time_in_seconds",
        "max_credit_supply",
        *GOVERNANCE_SURFACE.keys(),
    }

    sweep_combinations = len(sweep_params['label'])

    n_sweeps = N_SWEEP_SAMPLES if N_SWEEP_SAMPLES > 0 else sweep_combinations
    N_measurements = n_sweeps * TIMESTEPS * SAMPLES


    traj_combinations = n_sweeps * SAMPLES

    logger.info(f"PSuU Exploratory Run Dimensions: N_jobs={PROCESSES=:,}, N_t={TIMESTEPS=:,}, N_sweeps={n_sweeps:,}, N_mc={SAMPLES:,}, N_trajectories={traj_combinations:,}, N_measurements={N_measurements:,}")


    parallelize = PARALLELIZE
    use_joblib = USE_JOBLIB


    sim_start_time = datetime.now()
    logger.info(f"PSuU Exploratory Run starting at {sim_start_time}, ({sim_start_time - invoke_time} since invoke)")
    if parallelize is False:
        # Load simulation arguments
        sim_args = (
            INITIAL_STATE,
            sweep_params_samples,
            SUBSPACE_MODEL_BLOCKS,
            TIMESTEPS,
            SAMPLES,
        )
        # Run simulation and write results to disk
        sim_df = easy_run(
            *sim_args,
            exec_mode="single",
            assign_params=assign_params,
            deepcopy_off=True,
            supress_print=True
        )
    else:
        sweeps_per_process = SWEEPS_PER_PROCESS
        processes = PROCESSES

        chunk_size = sweeps_per_process
        split_dicts = [
            {k: v[i : i + chunk_size] for k, v in sweep_params_samples.items()}
            for i in range(0, len(list(sweep_params_samples.values())[0]), chunk_size)
        ]
        sim_folder_path = Path("data/simulations")
        base_folder = Path(f"psuu_run-{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}")
        output_folder_path =sim_folder_path / base_folder
        output_folder_path.mkdir(parents=True, exist_ok=True)

        output_path = str(output_folder_path / "timestep_tensor")

        def run_chunk(i_chunk, sweep_params, pickle_file=True, upload_to_s3=UPLOAD_TO_S3, post_process=True):
            logger.debug(f"{i_chunk}, {datetime.now()}")
            sim_args = (
                INITIAL_STATE,
                sweep_params,
                SUBSPACE_MODEL_BLOCKS,
                TIMESTEPS,
                SAMPLES,
            )
            # Run simulationz
            sim_df = easy_run(
                *sim_args,
                exec_mode="single",
                assign_params=assign_params,
                deepcopy_off=True,
                supress_print=True
            )

            if upload_to_s3:
                session = boto3.Session()
                s3 = session.client("s3")

            sim_df["subset"] = i_chunk * SWEEPS_PER_PROCESS + sim_df["subset"]
            output_filename = output_path + f"-{i_chunk}.pkl.gz"

            if pickle_file or upload_to_s3:
                sim_df.to_pickle(output_filename)
            if upload_to_s3:
                s3.upload_file(str(output_filename),
                CLOUD_BUCKET_NAME,
                str(base_folder / f"timestep_tensor-{i_chunk}.pkl.gz") 
                )
                os.remove(str(output_filename))


            if post_process:
                agg_df = timestep_tensor_to_trajectory_tensor(sim_df).reset_index()
                agg_output_filename = output_folder_path / f"trajectory_tensor-{i_chunk}.pkl.gz"
                if pickle_file:
                    agg_df.to_pickle(agg_output_filename)
                    if upload_to_s3:
                        s3.upload_file(str(agg_output_filename),
                                       CLOUD_BUCKET_NAME,
                                       str(base_folder / f"trajectory_tensor-{i_chunk}.pkl.gz"))

        args = enumerate(split_dicts)
        if use_joblib:
            Parallel(n_jobs=processes)(
                delayed(run_chunk)(i_chunk, sweep_params)
                for (i_chunk, sweep_params) in tqdm(args, desc='Simulation Chunks', total=len(split_dicts))
            )
        else:
            for i_chunk, sweep_params in tqdm(args):
                run_chunk(i_chunk, sweep_params)


        if RETURN_SIM_DF:
            sim_df = pd.concat(
                [pd.read_pickle(part, compression="gzip") for part in glob(output_path+"*")]
            )

    end_start_time = datetime.now()
    duration: float = (end_start_time - sim_start_time).total_seconds()
    logger.info(f"PSuU Run finished at {end_start_time}, ({end_start_time - sim_start_time} since sim start)")
    logger.info(f"PSuU Run Performance Numbers; Duration (s): {duration:,.2f}, Measurements Per Second: {N_measurements/duration:,.2f} M/s, Measurements per Job * Second: {N_measurements/(duration * PROCESSES):,.2f} M/(J*s)")
    if RETURN_SIM_DF:
        return sim_df # type: ignore
    else:
        pass

    if use_joblib and UPLOAD_TO_S3:
        files = glob(str(output_folder_path / f"trajectory_tensor-*.pkl.gz"))
        dfs = []
        for file in files:
            dfs.append(pd.read_pickle(file).reset_index())
        agg_df = pd.concat(dfs)
        agg_df.to_pickle(str(output_folder_path / f"trajectory_tensor.pkl.gz"))
        session = boto3.Session()
        s3 = session.client("s3")
        s3.upload_file(str(output_folder_path / f"trajectory_tensor.pkl.gz"),
                        CLOUD_BUCKET_NAME,
                        str(base_folder / f"trajectory_tensor.pkl.gz"))
    return None
