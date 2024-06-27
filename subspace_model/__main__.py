import logging

logger = logging.getLogger("subspace-digital-twin")
import glob

# logging.basicConfig(filename='cadcad.log', level=logging.INFO)
import os
from datetime import datetime

import click
import IPython
import pandas as pd

pd.set_option("display.width", None)
pd.set_option("display.max_columns", None)
# pd.set_option('display.max_rows', None)

from subspace_model.experiments.charts import (  # mc_total_supply,
    ab_block_utilization
)
from subspace_model.experiments.experiment import (
    sanity_check_run,
    sweep_credit_supply,
    initial_conditions,
    standard_stochastic_run,
    psuu,
)
from subspace_model.experiments.metrics import (
    profit1_mean,
    total_supply_max,
    total_supply_mean,
)

# Define a dictionary to map string log levels to their corresponding constants in logging module
log_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

experiments = {
    "sanity_check_run": sanity_check_run,
    "sweep_credit_supply": sweep_credit_supply,
    "initial_conditions": initial_conditions,
    "standard_stochastic_run": standard_stochastic_run,
    "psuu": psuu,
}

experiment_ids = {
    "sanity_check_run": 1,
    "standard_stochastic_run": 2,
    "fund_inclusion": 3,
    "reward_split_sweep": 4,
    "issuance_sweep": 5,
    "sweep_credit_supply": 6,
    # "sweep_over_single_component_and_credit_supply": 7,
    "initial_conditions": 8,
    # "sweep_over_single_component_and_credit_supply": 9,
    "reference_subsidy_sweep": 10,
}

experiment_charts = {
    "sanity_check_run": [],
    "standard_stochastic_run": [ab_block_utilization],
    "issuance_sweep": [],
    "fund_inclusion": [],
    "reward_split_sweep": [],
    "sweep_credit_supply": [ab_block_utilization],
    # "sweep_over_single_component_and_credit_supply": [],
    "initial_conditions": [],
    "reference_subsidy_sweep": [],
}

experiment_timestep_metrics = {
    "sanity_check_run": [],
    "standard_stochastic_run": [],
    "issuance_sweep": [],
    "fund_inclusion": [],
    "reward_split_sweep": [],
    "sweep_credit_supply": [],
    # "sweep_over_single_component_and_credit_supply": [],
    "initial_conditions": [],
    "reference_subsidy_sweep": [],
}

experiment_trajectory_metrics = {
    "sanity_check_run": [total_supply_mean, total_supply_max, profit1_mean],
    "standard_stochastic_run": [total_supply_mean, total_supply_max, profit1_mean],
    "issuance_sweep": [],
    "fund_inclusion": [],
    "reward_split_sweep": [],
    "sweep_credit_supply": [],
    # "sweep_over_single_component_and_credit_supply": [],
    "initial_conditions": [],
    "reference_subsidy_sweep": [],
}

experiment_additional_notebook_templates = {
    "sanity_check_run": [],
    "standard_stochastic_run": [],
    "issuance_sweep": [],
    "fund_inclusion": [],
    "reward_split_sweep": [],
    "sweep_credit_supply": [],
    # "sweep_over_single_component_and_credit_supply": [],
    "initial_conditions": [],
    "reference_subsidy_sweep": [],
}


def write_pickle_results(df, directory: str, filename: str):
    filepath = os.path.join(directory, filename)

    # Check if the directory exists, create it if it doesn't
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Save the DataFrame
    df.to_pickle(filepath, compression="gzip")
    logger.info(f"Results saved to {filepath}.")


def find_latest_simulation(experiment: str) -> str | None:
    pattern = f"data/simulations/{experiment}-*.pkl.gz"
    files = glob.glob(pattern)

    if experiment not in list(experiments.keys()):
        logger.warning(
            f"Experiment {experiment} not found. Try one of: {list(experiments.keys())}"
        )
        return None

    if not files:
        logger.warning(
            f"No data found for experiment: {experiment}. Try generating data with `python -m subspace_model -e {experiment}"
        )
        return None

    # Get the most recent file based on modification time
    latest_file = max(files, key=os.path.getmtime)

    # Get the timestamp of the experiment
    timestamp = "-".join(latest_file.split("-")[1:]).replace(".pkl.gz", "")

    return timestamp


def get_charts(df: pd.DataFrame, experiment: str):
    charts = [
        (plot.__name__, plot(df, experiment)) for plot in experiment_charts[experiment]
    ]

    return charts


def save_charts(experiment: str):
    logger.info(f"Visualizing experiment: {experiment}...")
    latest_simulation_timestamp = find_latest_simulation(experiment)
    if latest_simulation_timestamp is not None:
        latest_simulation = (
            f"data/simulations/{experiment}-{latest_simulation_timestamp}.pkl.gz"
        )
        df = pd.read_pickle(latest_simulation)

        # Check if the directory exists, create it if it doesn't
        directory = f"data/charts/"
        if not os.path.exists(directory):
            os.makedirs(directory)

        charts = get_charts(df, experiment)
        for chart_name, chart in charts:
            logger.info(f"Generating chart {chart_name} for experiment {experiment}...")
            chart.write_image(
                f"{directory}{experiment}-{latest_simulation_timestamp}-{chart_name}.png"
            )


def run_calculate_metrics(sim_df: pd.DataFrame, experiment: str):
    logger.info(f"Running metrics calculations for {experiment}...")

    # Timestep metrics
    timestep_metrics = experiment_timestep_metrics[experiment]
    if len(timestep_metrics):
        timestep_metrics_df = pd.concat(
            [metrics(sim_df) for metrics in timestep_metrics], axis=1
        )
    else:
        timestep_metrics_df = pd.DataFrame()
    logger.info(f"Timestep metrics for {experiment}:")
    logger.info(timestep_metrics_df)

    # Trajectory metrics
    trajectory_metrics = experiment_trajectory_metrics[experiment]
    if len(trajectory_metrics):
        trajectory_metrics_df = pd.concat(
            [metrics(sim_df) for metrics in experiment_trajectory_metrics[experiment]],
            axis=1,
        ).T
    else:
        trajectory_metrics_df = pd.DataFrame()
    logger.info(f"Trajectory metrics for {experiment}:")
    logger.info(trajectory_metrics_df)
    logger.info(f"Finished metrics calculations for {experiment}...")
    return timestep_metrics_df, trajectory_metrics_df


def run_experiment(
    experiment: str, samples: int | None = None, days: int | None = None, sweep_samples: int | None = None, RETURN_SIM_DF: bool = False
):
    """
    Run an experiment with for a given number of days and samples.
    """
    logger.info(f"Executing experiment: {experiment}...")
    experiment_run = experiments[experiment]

    kwargs = dict(SAMPLES=samples,
                  SIMULATION_DAYS=days,
                  N_SWEEP_SAMPLES=sweep_samples,
                  RETURN_SIM_DF=RETURN_SIM_DF,
                  )
    
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    df = experiment_run(**kwargs)

    logger.info(f"{experiment} executed.")

    return df


def process_experiment(
    visualize: bool,
    experiment: str,
    pickle: bool,
    calculate_metrics: bool,
    generate_notebooks: bool = False,
    generate_template: bool = False,
    samples: int | None = None,
    days: int | None = None,
    sweep_samples: int | None = None
):
    if generate_notebooks:
        generate_notebooks_from_templates(experiment)
        return
    elif generate_template:
        generate_template_from_notebook(experiment)
        return
    elif visualize:
        save_charts(experiment)
        return
    else:
        sim_df = run_experiment(experiment, samples, days, sweep_samples, RETURN_SIM_DF=pickle)
        if calculate_metrics:
            timestep_metrics_df, trajectory_metrics_df = run_calculate_metrics(
                sim_df,
                experiment,
            )

        # Conditionally pickle the results
        if pickle:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            write_pickle_results(
                sim_df,
                directory="data/simulations/",
                filename=f"{experiment}-{timestamp}.pkl.gz",
            )
        if pickle and calculate_metrics:
            write_pickle_results(
                timestep_metrics_df,
                directory="data/metrics/",
                filename=f"{experiment}-timestep-metrics-{timestamp}.pkl.gz",
            )
            write_pickle_results(
                trajectory_metrics_df,
                directory="data/metrics/",
                filename=f"{experiment}-trajectory-metrics-{timestamp}.pkl.gz",
            )


def generate_notebooks_from_templates(experiment: str):
    logger.info(f"Generating notebooks for {experiment}")
    id = "{:02d}".format(experiment_ids[experiment])
    template_names = [f"{id}-{experiment}"]
    # template_names.append(experiment_additional_notebook_templates[experiment])
    for template_name in template_names:
        notebook = f"./notebooks/{template_name}.ipynb"
        template = f"./notebook_templates/{template_name}.py"
        CMD = f"""cat {template} |
        jupytext --from py:percent --to ipynb --set-kernel - |
        papermill - {notebook} --cwd notebooks/"""
        logger.info(CMD)
        os.system(CMD)


def generate_template_from_notebook(experiment: str):
    logger.info(f"Generating notebooks for {experiment}")
    id = "{:02d}".format(experiment_ids[experiment])
    template_name = f"{id}-{experiment}"
    notebook = f"notebooks/{template_name}.ipynb"
    template = f"notebook_templates/{template_name}.py"
    CMD = f"""cat {notebook} | papermill - {notebook} --cwd notebooks/ -p nb_name {template_name} && cat {notebook} |
    jupytext --from ipynb --to py:percent --set-kernel - > {template}"""
    print(CMD)
    os.system(CMD)


@click.command()
@click.option(
    "-e",
    "--experiment",
    "experiment",
    type=click.Choice(experiments.keys(), case_sensitive=False),
    default="sanity_check_run",
    help="Select an experiment to run.",
)
@click.option(
    "-p",
    "--pickle",
    "pickle",
    default=False,
    is_flag=True,
    help="Pickle results to data/simulations/.",
)
@click.option(
    "-i",
    "--interactive",
    "interactive",
    default=False,
    is_flag=True,
    hidden=True,
    help="Drop into an IPython shell for interactive exploration.",
)
@click.option(
    "-l",
    "--log-level",
    "log_level",
    type=click.Choice(log_levels.keys(), case_sensitive=False),
    default="info",
    hidden=True,
    help="Set the logging level.",
)
@click.option(
    "-a",
    "--run-all",
    "run_all",
    default=False,
    is_flag=True,
    help="Run all experiments.",
)
@click.option(
    "-v",
    "--visualize",
    "visualize",
    default=False,
    is_flag=True,
    hidden=True,
    help="Visualize the most recent results of the selected experiment. Combine with -e or -a to select which experiment results to visualize.",
)
@click.option(
    "-s",
    "--samples",
    "samples",
    default=None,
    type=int,
    help="Set Sample size; if not set runs default sample size.",
)
@click.option(
    "-d",
    "--days",
    "days",
    default=None,
    type=int,
    help="Number of simulation days.",
)
@click.option(
    "-m",
    "--metrics",
    "calculate_metrics",
    default=False,
    is_flag=True,
    hidden=True,
    help="Run experiment metrics calculations. Optionally save to disk with -p.",
)
@click.option(
    "-gn",
    "--generate_notebooks",
    "generate_notebooks",
    default=False,
    is_flag=True,
    hidden=True,
    help="Generate notebooks from templates.",
)
@click.option(
    "-gt",
    "--generate_template",
    "generate_template",
    default=False,
    is_flag=True,
    hidden=True,
    help="Generate template from notebook.",
)
@click.option(
    "-sw",
    "--sweep_samples",
    "sweep_samples",
    default=10,
    type=int,
    help="Number of sweep combinations to sample (if applicable for the experiment)",
)
def main(
    experiment: str,
    pickle: bool,
    interactive: bool,
    log_level: str,
    run_all: bool,
    visualize: bool,
    samples: int | None,
    days: int | None,
    calculate_metrics: bool,
    generate_notebooks: bool,
    generate_template: bool,
    sweep_samples: int
) -> None:
    # Initialize logging

    logger.info(f"Initializing main...")
    logger.info(f"Setting log level to {log_level}...")
    logger.setLevel(log_levels[log_level])

    # All experiments selected
    if run_all:
        for experiment in list(experiments.keys()):
            process_experiment(
                visualize,
                experiment,
                pickle,
                calculate_metrics,
                generate_notebooks,
                generate_template,
                samples,
                days,
                sweep_samples
            )

    # Single experiment selected
    else:
        process_experiment(
            visualize,
            experiment,
            pickle,
            calculate_metrics,
            generate_notebooks,
            generate_template,
            samples,
            days,
            sweep_samples
        )

    # Conditionally drop into an IPython shell
    if interactive:
        IPython.embed()


if __name__ == "__main__":
    main()
