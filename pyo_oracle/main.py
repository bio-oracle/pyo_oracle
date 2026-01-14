"""
Main module with library functions.
"""

import re
from functools import lru_cache
from glob import glob
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    get_args,
    overload,
)

import pandas as pd

from pyo_oracle._config import config
from pyo_oracle.utils import (
    _download_layer,
    _ensure_hashable,
    _layer_dataframe,
    _validate_argument,
    confirm,
    convert_bytes,
    verbose_print,
)

# Literal typing for type checking and validation (using _validate_argument)
_Variable = Literal[
    "chl",
    "clt",
    "dfe",
    "mlotst",
    "no3",
    "o2",
    "ph",
    "phyc",
    "po4",
    "si",
    "siconc",
    "sithick",
    "so",
    "swd",
    "sws",
    "tas",
    "terrain",
    "thetao",
]
_SSP = Literal["ssp119", "ssp126", "ssp245", "ssp370", "ssp460", "ssp585", "baseline"]
_TimePeriod = Literal["present", "future"]
_Depth = Literal["min", "mean", "max", "surf"]


def download_layers(
    dataset_ids: Union[str, Iterable[str]],
    output_directory: Union[str, Path] = None,
    response: str = "nc",
    constraints: Dict[str, Any] = None,
    skip_confirmation: bool = None,
    verbose: bool = True,
    log: bool = True,
    timestamp: bool = True,
    timeout: int = 120,
    skip_convert_to_lowercase: bool = False,
    **httpx_kwargs,
) -> None:
    """
    Downloads one or more layers.

    Args:
        dataset_ids (str or list): Dataset ID(s) to download. A single dataset ID or a list of IDs.
        output_directory (str or Path, optional): Directory where downloaded files will be saved. If not provided, the default directory will be used.
        response (str, optional): Format of the response to download. Default is 'nc'.
        constraints (dict, optional): Constraints to apply to the downloaded data.
        skip_confirmation (bool, optional): If True, confirmation prompts will be skipped. If None, the value from the configuration will be used.
        verbose (bool, optional): If True, detailed information will be printed during the download process.
        log (bool, optional): If True, a log of the download will be created.
        timestamp (bool, optional): If True, a timestamp will be added to the downloaded files' names.
        timeout (int, optional): Timeout in seconds for the download request.
        skip_convert_to_lowercase (bool, optional): If True, the dataset ID will not be converted to lowercase.
        httpx_kwargs (dict, optional): Additional keyword arguments to pass to the httpx function.

    Returns:
        None

    Note:
        This function downloads the specified dataset(s) and saves them to the provided or default output directory.

    Example:
        # Download a single dataset with default settings
        download_layers(dataset_ids="dataset123")

        # Download multiple datasets with custom settings
        download_layers(dataset_ids=["dataset456", "dataset789"], output_directory="/path/to/output", response="csv", verbose=False)
    """
    if isinstance(dataset_ids, str):
        dataset_ids = (dataset_ids,)

    if skip_confirmation is None:
        skip_confirmation = eval(config["skip_confirmation"])

    if not skip_confirmation and not constraints:
        question = "No constraints have been set. This will download the full dataset, which may be a few GBs in size."

        if not confirm(question):
            return

    for dataset_id in dataset_ids:
        if not dataset_id.islower() and not skip_convert_to_lowercase:
            print(f"Converting dataset ID '{dataset_id}' to lowercase.")
            dataset_id = dataset_id.lower()
        _download_layer(
            dataset_id,
            output_directory,
            response,
            constraints,
            skip_confirmation,
            verbose,
            log,
            timestamp,
            timeout,
            **httpx_kwargs,
        )


# With overloading, we can match the different results of the function
# based on the argument dataframe=True/False.
@overload
def list_layers(
    search: Optional[Union[str, Iterable[str]]] = None,
    variables: Optional[Union[_Variable, Iterable[_Variable]]] = None,
    ssp: Optional[Union[_SSP, Iterable[_SSP]]] = None,
    time_period: Optional[_TimePeriod] = None,
    depth: Optional[Union[_Depth, Iterable[_Depth]]] = None,
    dataframe: Literal[True] = True,
    simplify: bool = False,
    _include_allDatasets: bool = False,
) -> pd.DataFrame: ...


@overload
def list_layers(
    search: Optional[Union[str, Iterable[str]]] = None,
    variables: Optional[Union[_Variable, Iterable[_Variable]]] = None,
    ssp: Optional[Union[_SSP, Iterable[_SSP]]] = None,
    time_period: Optional[_TimePeriod] = None,
    depth: Optional[Union[_Depth, Iterable[_Depth]]] = None,
    dataframe: Literal[False] = False,
    simplify: bool = False,
    _include_allDatasets: bool = False,
) -> List[str]: ...


def list_layers(
    search: Optional[Union[str, Iterable[str]]] = None,
    variables: Optional[Union[_Variable, Iterable[_Variable]]] = None,
    ssp: Optional[Union[_SSP, Iterable[_SSP]]] = None,
    time_period: Optional[_TimePeriod] = None,
    depth: Optional[Union[_Depth, Iterable[_Depth]]] = None,
    dataframe: bool = True,
    simplify: bool = False,
    _include_allDatasets: bool = False,
) -> Union[pd.DataFrame, List[str]]:
    """
    Lists available layers in the Bio-ORACLE server.

    Args:
        search (str|list): Natural text search term, eg. 'Temperature', 'Oxygen'.
        variables (str|list): Variables to filter from. Valid values are ['po4','o2','si','ph','sws','phyc','so','thetao','dfe','no3','sithick','tas','siconc','chl','mlotst','clt','terrain'].
        ssp (str|list): Future scenario to choose from. Valid values are ['ssp119', 'ssp126', 'ssp370', 'ssp585', 'ssp460', 'ssp245', 'baseline'].
        time_period (str): Time period to choose from. Valid values are either 'present' or 'future'.
        depth (str|list): Depth category to choose from. Valid values are ['min', 'mean', 'max', 'surf'].
        dataframe (bool): Whether to return a Pandas DataFrame. If False, will return a list.
        simplify (bool): Whether to simplify the output. If True, will return only dataset ID and dataset title. If dataframe=False, this doesn't do anything.
        _include_allDatasets (bool): Internal flag for including all datasets.

    Returns:
        pd.DataFrame or list: If 'dataframe' is True (default), returns a Pandas DataFrame containing filtered layers' information. If 'dataframe' is False, returns a list of filtered dataset IDs.

    Notes:
        - This function queries the Bio-ORACLE server to list available layers based on the provided filters.
        - Filtering can be done by specifying 'variables', 'ssp', and 'time_period'.
        - The function provides flexibility in choosing to return a DataFrame or a list of dataset IDs.

    Example:
        # List all available layers
        all_layers = list_layers()

        # List layers for specific variables and future scenarios
        filtered_layers = list_layers(variables=['po4', 'o2'], ssp='ssp585', dataframe=True)
    """

    # Validate the provided arguments against valid values
    _valid_args = {
        # With get_args, we get the list of valid arguments using the Literal type
        "valid_variables": get_args(_Variable),
        "valid_ssp": get_args(_SSP),
        "valid_time_period": get_args(_TimePeriod),
        "valid_depth": get_args(_Depth),
    }
    names = ("variables", "ssp", "time_period", "depth")
    values = (variables, ssp, time_period, depth)
    for name, value in zip(names, values):
        _validate_argument(name, value, _valid_args[f"valid_{name}"])

    # Convert inputs into a hashable tuple for caching.
    # The main logic is defined in _list_layers.
    return _list_layers(
        _ensure_hashable(search),
        _ensure_hashable(variables),
        _ensure_hashable(ssp),
        _ensure_hashable(time_period),
        _ensure_hashable(depth),
        dataframe,
        simplify,
        _include_allDatasets,
    )


# Auxiliary function for caching.
@lru_cache(maxsize=8)
def _list_layers(
    search: Optional[Tuple[str, ...]] = None,
    variables: Optional[Tuple[_Variable, ...]] = None,
    ssp: Optional[Tuple[_SSP, ...]] = None,
    time_period: Optional[Tuple[_TimePeriod]] = None,
    depth: Optional[Tuple[_Depth, ...]] = None,
    dataframe: bool = True,
    simplify: bool = False,
    _include_allDatasets: bool = False,
) -> Union[pd.DataFrame, List[str]]:

    # Fetch the dataframe containing layer information
    _dataframe = _layer_dataframe(_include_allDatasets)

    if search:
        search_terms = search if isinstance(search, (tuple, list)) else (search,)
        pattern = "|".join(re.escape(term) for term in search_terms)
        searchable_columns = [
            col
            for col in ("datasetID", "title", "long_name", "standard_name")
            if col in _dataframe.columns
        ]
        if not searchable_columns:
            searchable_columns = ["datasetID"]

        mask = pd.Series(False, index=_dataframe.index)
        for col in searchable_columns:
            mask = mask | _dataframe[col].str.contains(pattern, case=False, na=False)
        _dataframe = _dataframe[mask]

    # Filter the resulting dataframe based on provided filters
    if variables:
        _dataframe = pd.concat(
            [
                _dataframe[_dataframe["datasetID"].str.startswith(v.lower())]
                for v in variables
            ]
        )
    if time_period:
        start_decade = _dataframe["datasetID"].str.split("_", expand=True)[2]
        if time_period == ("present",):
            _dataframe = _dataframe[start_decade == "2000"]
        elif time_period == ("future",):
            _dataframe = _dataframe[start_decade == "2020"]
    if ssp:
        _dataframe = pd.concat(
            [
                _dataframe[
                    (_dataframe["datasetID"].str.contains(v.lower()))
                    | (_dataframe["datasetID"].str.contains(v.capitalize()))
                    | (_dataframe["datasetID"].str.contains(v.upper()))
                ]
                for v in ssp
            ]
        )
    if depth:
        _dataframe = pd.concat(
            [
                _dataframe[
                    (_dataframe["datasetID"].str.contains("depth" + v.lower()))
                    | (_dataframe["datasetID"].str.contains("depth" + v.capitalize()))
                    | (_dataframe["datasetID"].str.contains("depth" + v.upper()))
                ]
                for v in depth
            ]
        )

    # Convert to list if needed
    if dataframe:
        # Simplify option
        if simplify:
            _dataframe = _dataframe[["datasetID", "title"]]
        return _dataframe.reset_index(drop=True)
    else:
        return _dataframe["datasetID"].to_list()


def list_local_data(data_directory: Optional[Union[str, Path]] = None, verbose: bool = True):
    """
    Lists datasets that are locally downloaded.

    Args:
        data_directory (str, optional): Path to the data directory. If not provided, the path from the configuration will be used.
        verbose (bool): If True, detailed information will be printed. If False, only basic file names will be printed.

    Returns:
        None

    Note:
        This function lists the datasets available in the specified data directory.

    Example:
        # List all datasets in the default data directory with detailed information
        list_local_data()

        # List datasets in a specific directory without verbose output
        list_local_data(data_directory="/path/to/data", verbose=False)
    """
    if data_directory is None:
        data_directory = config["data_directory"]

    verbose_print(f"Your data directory is '{data_directory}'.\n", verbose)
    verbose_print("Contents of data directory:", verbose)
    files = glob(str(Path(config["data_directory"]).joinpath("*")))
    if not verbose:
        files = [f for f in files if not str(f).endswith(".log")]
    if files:
        for file in files:
            print(
                "\t", Path(file).name, "\t", convert_bytes(Path(file).stat().st_size)
            ) if verbose else print("\t", Path(file).name)
        print()
    else:
        print(f"Data directory at '{data_directory}' does not contain any data.")
    if verbose:
        dirsize = sum(Path(f).stat().st_size for f in files)
        dirsize = convert_bytes(dirsize)
        verbose_print(f"Size of data directory is {dirsize}.", verbose)
