"""
Utitilies and private methods that are used internally.
"""

from copy import deepcopy
from datetime import datetime
from functools import lru_cache
from glob import glob
import logging
from pathlib import Path

import httpx

from pyo_oracle.config import default_server, config


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc

    from https://stackoverflow.com/questions/2104080/how-do-i-check-file-size-in-python
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def _format_args(function):
    """
    Converts list/str to tuple.

    This is used as we want functions to work on multiple items, but also want to allow users
    to pass strings.

    Prevent TypeError when passing list to function with lru_cache.

    From: https://stackoverflow.com/questions/49210801/python3-pass-lists-to-function-with-functools-lru-cache
    """
    def wrapper(*args, **kwargs):
        kwargs = {k: tuple(x) if type(x) == list else x for k, x in kwargs.items()}
        kwargs = {k: (x,) if type(x) == str else x for k, x in kwargs.items()}
        args = [tuple(x) if type(x) == list else x for x in args]
        args = [(x,) if type(x) == str else x for x in args]
        result = function(*args, **kwargs)
        return result
    return wrapper


def _validate_argument(name: str, value: str or list or tuple, valid_values: list):
    """Check if argument is in a valid list of values."""
    if value:
        for v in value:
            if v.lower() not in valid_values:
                print(f"Selected {name} '{v}' is not a valid {name}. These are valid values:\n{valid_values}")



def _download_file_from_url(url: str, local_path: Path):
    """
    Downloads a large file from a URL.
    From: https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    """
    with open(local_path, "wb") as f:
        with httpx.stream("GET", url) as response:
            for chunk in response.iter_bytes():
                f.write(chunk)
    return local_path


# Small helpers
verbose_print = lambda message, verbose: print(message) if verbose else None
info_logger = lambda msg, log: logging.info(msg) if log else None
def confirm(msg, cancel_msg="Download cancelled."):
    response = input(msg + " Would you like to proceed? y/N")
    if response.lower() in "y yes".split():
        return True
    else:
        print(cancel_msg)
        return False


def _get_griddap_dataset_url(
    dataset_id,
    variables=None,
    constraints=None,
    response="nc",
    verbose=False,
):

    server = deepcopy(default_server)
    server.dataset_id = dataset_id
    server.protocol = "griddap"
    server.griddap_initialize()

    verbose_print(f"Selected '{dataset_id}' dataset.", verbose)
    verbose_print(f"Dataset info available at: {server.get_info_url()}", verbose)

    # Setting constraints that match
    if constraints:
        constraints = {**server._constraints_original, **constraints}
        for k, v in constraints.items():
            if k in server.constraints.keys():
                server.constraints[k] = v
                server._constraints_original[k] = v

    # The same for variables
    if variables:
        server.variables = [v for v in server.variables if v in variables]
    verbose_print(
        f"Selected {len(server.variables)} variables: {server.variables}.", verbose
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


def _download_layer(dataset_id: str or list, output_directory: str or Path = None, response: str = "nc", constraints: dict = None, skip_confirmation=False, verbose=True, log=True, timestamp=True):
    timestamp = datetime.now().isoformat(timespec='seconds')
    filename = f"{dataset_id}_{timestamp}.{response}" if timestamp else f"{dataset_id}.{response}"
    outdir = Path(output_directory) if output_directory else Path(config["data_directory"])
    local_path = outdir.joinpath(filename)

    # Check for existing layers
    if not skip_confirmation:
        print()
        print(f"Data directory is '{outdir}'.", end="\n\n")
        existing_layers = [i for i in outdir.iterdir() if str(i.name).startswith(dataset_id) and not str(i.name).endswith(".log")]
        print(f"You have {len(existing_layers)} local datasets with the same preffix as '{dataset_id}' in the data directory:")
        for layer in existing_layers:
            print(layer.name, "\t", convert_bytes(layer.stat().st_size))
        print()
        print("You can check it again by running `list_local_data()`.")
        print("To check the constraints of each existing dataset, see the log files in the data directory.", end="\n\n")

        msg = ""
        if not confirm(msg):
            return

    # Configure logging
    logfile = local_path.with_suffix(".log")
    logging.basicConfig(filename=logfile, format="%(asctime)s %(message)s", level=logging.INFO)

    msg = f"Downloading dataset '{dataset_id}' as {response} file to '{outdir}'."
    info_logger(msg, log)
    verbose_print(msg, verbose)

    msg = "Constraints are:"
    info_logger(msg, log)
    verbose_print(msg, verbose)
    info_logger(constraints, log)
    verbose_print(constraints, verbose)

    url = _get_griddap_dataset_url(dataset_id, constraints=constraints, response=response)  # Response is converted to 
    _download_file_from_url(url, local_path)
    if (verbose or log) and local_path.exists():
        filesize = convert_bytes(local_path.stat().st_size)
        msg = f"Download finished at '{local_path}'. File size is {filesize}."
        info_logger(msg, log)
        verbose_print(msg, verbose)
