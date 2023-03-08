"""
Main module with library functions.
"""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

import httpx
import pandas as pd
from erddapy import ERDDAP

from bio_oracle_py.config import config


default_server = ERDDAP(
    server=config["erddap_server"],
)


def download_layers(dataset_id: str or list, response: str = "nc"):
    """
    Downloads one or more layers.
    """
    if isinstance(dataset_id, str):
        dataset_id = [dataset_id,]

    s = deepcopy(default_server)
    for dataset in dataset_id:
        url = _get_griddap_dataset_url(dataset, response=response)
        filename = f"{dataset_id}.{response}"
        local_path = Path(config["data_directory"]).joinpath(filename)
        _download_file_from_url(url, local_path)
        


def _download_file_from_url(url: str, local_path: Path):
    """
    Downloads a large file from a URL.
    From: https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    """
    # NOTE the stream=True parameter below
    with httpx.get(url, stream=True) as r:
        r.raise_for_status()
        print(f"Writing to '{local_path}'.\n")
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return local_path    


def _get_griddap_dataset_url(
    dataset_id,
    variables=None,
    constraints=None,
    response="nc",
    _print=False,
):
    printer = lambda message: print(message) if _print else None

    server = deepcopy(default_server)
    server.dataset_id = dataset_id
    server.protocol = "griddap"
    server.griddap_initialize()

    printer(f"Selected '{dataset_id}' dataset.")
    printer(f"Dataset info available at: {server.get_info_url()}")

    # Setting constraints that match
    if constraints:
        for k, v in constraints.items():
            if k in server.constraints.keys():
                server.constraints[k] = v

    # The same for variables
    if variables:
        server.variables = [v for v in server.variables if v in variables]
    printer(
        f"Selected {len(server.variables)} variables: {server.variables}."
    )
    url = server.get_download_url(response=response)
    return url


@lru_cache(2)
def _layer_dataframe(include_allDatasets=False):
    """
    Requests the list of layers as a pandas DataFrame.
    
        include_allDatasets (bool): whether to include the row with the 'allDatasets' dataset.
    """
    s = deepcopy(default_server)
    s.dataset_id = "allDatasets"
    s.protocol = "tabledap"
    df = s.to_pandas()

    if not include_allDatasets:
        df = df.iloc[1:]
    return df


def _validate_argument(name: str, value: str or list, valid_values: list):
    """Check if argument is in a valid list of values."""
    if value:
        if isinstance(value, str):
            value = [value,]
        for v in value:
            if v.lower() not in valid_values:
                print(f"Selected {name} '{v}' is not a valid {name}. These are valid values:\n{valid_values}")


@lru_cache(8)
def list_layers(variables: str or list = None, ssp: str or list = None, time_period: str = None, dataframe_response: bool = True, _include_allDatasets: bool = False) -> pd.DataFrame or list:
    """
    Lists available layers in the Bio-ORACLE server.

        variables (str|list): variables to filter from. Valid values are ['po4','o2','si','ph','sws','phyc','so','thetao','dfe','no3','sithick','tas','siconc','chl','mlotst','clt','terrain'].
        ssp (str|list): future scenario to choose from. Valid values are ['ssp119', 'ssp126', 'ssp370', 'ssp585', 'ssp460', 'ssp245', 'baseline'].
        time_period (str): time period to choose from. Valie values are either 'present' or 'future'.
        dataframe_response (bool): whether to return a Pandas Dataframe. If False, will return a list.
    """
    valid_variables = ['po4','o2','si','ph','sws','phyc','so','thetao','dfe','no3','sithick','tas','siconc','chl','mlotst','clt','terrain']
    valid_ssp = ['ssp119', 'ssp126', 'ssp370', 'ssp585', 'ssp460', 'ssp245', 'baseline']
    valid_time_period = "present future".split()

    for arg in "variables", "ssp", "time_period":
        _validate_argument(arg, eval(arg), eval(f"valid_{arg}"))

    dataframe = _layer_dataframe(_include_allDatasets)
    # Filter resulting dataframe
    if variables:
        dataframe = pd.concat([dataframe[dataframe["datasetID"].str.startswith(v.lower())] for v in variables])
    if time_period:
        start_decade = dataframe["datasetID"].str.split("_", expand=True)[3]
        if time_period == "present":
            return dataframe[start_decade == "2000"]
        elif time_period == "future":
            return dataframe[start_decade == "2020"]
    if ssp:
        dataframe = pd.concat([dataframe[(dataframe["datasetID"].str.contains(v.lower())) | (dataframe["datasetID"].str.contains(v.capitalize())) | (dataframe["datasetID"].str.contains(v.upper()))] for v in ssp])

    # Convert to list
    if dataframe_response:
        return dataframe.reset_index(drop=True)
    else:
        return dataframe["datasetID"].to_list()


def list_local_data():
    """
    Lists datasets that are locally downloaded.
    """
    pass
