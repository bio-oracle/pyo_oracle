"""
Main module with library functions.
"""
from copy import deepcopy

import pandas as pd
from erddapy import ERDDAP

from bio_oracle_py.config import config


default_server = ERDDAP(
    server=config["erddap_server"],
)


def download_layers(dataset_id: str or list):
    """
    Downloads one or more layers.
    """
    pass


def list_layers(dataframe_response: bool = True, variables: str or list = None, ssp: str or list = None, time_period: str = None) -> pd.DataFrame or list:
    """
    Lists available layers in the Bio-ORACLE server.

        dataframe_response (bool): whether to return a Pandas Dataframe. If False, will return a list.
        variables (str|list): variables to filter from. Valid values are ['po4','o2','si','ph','sws','phyc','so','thetao','dfe','no3','sithick','tas','siconc','chl','mlotst','clt','terrain'].
        ssp (str|list): future scenario to choose from. Valid values are ['ssp119', 'ssp126', 'ssp370', 'ssp585', 'ssp460', 'ssp245', 'baseline'].
        time_period (str): time period to choose from. Valie values are either 'present' or 'future'.
    """
    # Input validation
    if variables:
        valid_variables = ['po4','o2','si','ph','sws','phyc','so','thetao','dfe','no3','sithick','tas','siconc','chl','mlotst','clt','terrain']
        if isinstance(variables, str):
            variables = [variables,]
        for v in variables:
            if v.lower() not in valid_variables:
                print(f"Selected variable '{v}' is not a valid variable. These are valid values:\n{valid_variables}")
    if time_period:
        valid_time_periods = "present future".split()
        if time_period.lower() not in valid_time_periods:
            print(f"Selected time period '{time_period}' is not a valid time period. These are valid values:\n{valid_time_periods}")
    if ssp:
        valid_ssps = ['ssp119', 'ssp126', 'ssp370', 'ssp585', 'ssp460', 'ssp245', 'baseline']
        if isinstance(ssp, str):
            ssp = [ssp,]
        for v in ssp:
            if v.lower() not in valid_ssps:
                print(f"Selected SSP '{v}' is not a valid variable. These are valid values:\n{valid_ssps}")

    # Make the request from new server instance
    s = deepcopy(default_server)
    s.dataset_id = "allDatasets"
    s.protocol = "tabledap"
    dataframe = s.to_pandas()

    # Filter resulting dataframe
    if variables:
        dataframe = pd.concat([dataframe[dataframe["datasetID"].str.startswith(v.lower())] for v in variables])
    if time_period:
        decades = dataframe["datasetID"].str.split("_", expand=True)[3]
        if time_period == "present":
            return dataframe[decades == "2000"]
        elif time_period == "future":
            return dataframe[decades == "2020"]
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
