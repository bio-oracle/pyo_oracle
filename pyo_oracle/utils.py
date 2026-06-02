"""
Utilities and private methods that are used internally.
"""

import logging
import warnings
from copy import deepcopy
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Container, Dict, Iterable, Optional, Tuple, Union

import httpx
import pandas as pd

from pyo_oracle._config import config, default_server


def convert_bytes(num: float) -> str:
    """
    Convert bytes to human-readable file sizes (e.g., KB, MB, GB, etc.).

    Args:
        num (float): Size in bytes.

    Returns:
        str: Human-readable file size representation.

    Reference:
        https://stackoverflow.com/questions/2104080/how-do-i-check-file-size-in-python
    """
    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def _ensure_hashable(
    value: Optional[Union[Iterable[str], str]]
) -> Optional[Tuple[str, ...]]:
    """
    Ensure that the value is hashable.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable):
        return tuple(sorted(value))
    raise ValueError(f"Value {value} cannot be transformed into a hashable tuple.")


def _validate_argument(
    name: str, value: Optional[Union[str, Iterable[str]]], valid_values: Container[str]
) -> None:
    """
    Check if an argument is in a valid list of values.

    Args:
        name (str): Name of the argument being validated.
        value (str or iterable of str): Value(s) of the argument to validate.
        valid_values (container of str): Container of valid values for the argument.

    Returns:
        None
    """
    if value is None:
        return

    msg = "Selected {name} '{value}' is not a valid {name}. These are valid values:\n{valid_values}"

    if isinstance(value, str):
        if value.lower() not in valid_values:
            print(msg.format(name=name, value=value, valid_values=valid_values))
        return

    if isinstance(value, Iterable):
        for v in value:
            if v.lower() not in valid_values:
                print(msg.format(name=name, value=v, valid_values=valid_values))
        return


def _download_file_from_url(url: str, local_path: Path, **httpx_kwargs) -> Path:
    """
    Downloads a large file from a URL.

    Args:
        url (str): URL of the file to download.
        local_path (Path): Local path to save the downloaded file.
        httpx_kwargs: keyword arguments for the httpx.stream function.

    Returns:
        Path: Path to the downloaded local file.
    """
    with open(local_path, "wb") as f:
        with httpx.stream(
            "GET", url, follow_redirects=True, **httpx_kwargs
        ) as response:
            for chunk in response.iter_bytes():
                f.write(chunk)
    return local_path


# Small helpers
def verbose_print(message: Any, verbose: bool) -> None:
    """Print ``message`` only when ``verbose`` is True."""
    if verbose:
        print(message)


def info_logger(msg: Any, log: bool) -> None:
    """Log ``msg`` at INFO level only when ``log`` is True."""
    if log:
        logging.info(msg)


def confirm(msg: str, cancel_msg: str = "Download cancelled.") -> bool:
    """
    Prompt the user for confirmation to proceed.

    Args:
        msg (str): The message to display as the confirmation prompt.
        cancel_msg (str, optional): The message to display when the user cancels the operation. Default is "Download cancelled."

    Returns:
        bool: True if the user confirms, False otherwise.
    """
    print(
        "You can disable these confirmation prompts by passing 'skip_confirmation=True' to the function,"
        " or set the 'skip_confirmation' setting to True in the config.ini file.\n"
    )
    response = input(msg + " Would you like to proceed? y/N\n")
    if response.lower() in "y yes".split():
        return True
    else:
        print(cancel_msg)
        return False


def _as_bool(value: Any) -> bool:
    """
    Safely coerce a config/CLI value to a boolean.

    Replaces the previous ``eval(...)`` based parsing, which was unsafe and
    failed on values such as the string ``"false"``.

    Args:
        value: A value that may be a bool, or a string such as "True"/"false"/"1".

    Returns:
        bool: The parsed boolean value.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


def _build_griddap_server(
    dataset_id: str,
    variables: Optional[Container[str]] = None,
    constraints: Optional[Dict[str, Any]] = None,
    verbose: bool = False,
):
    """
    Build and configure an erddapy ``ERDDAP`` server for a griddap dataset.

    This is the single, shared code path used by ``_get_griddap_dataset_url``,
    ``load_layer`` and ``_layer_info`` so that the (somewhat fragile) handling
    of erddapy's private ``_constraints_original`` lives in exactly one place.

    Args:
        dataset_id (str): The ID of the dataset.
        variables (container of str, optional): Variable names to select. If None, all are kept.
        constraints (dict[str, Any], optional): Constraints to apply on top of the dataset defaults.
        verbose (bool, optional): If True, print selection details.

    Returns:
        erddapy.ERDDAP: A configured server instance with ``protocol='griddap'``.
    """
    server = deepcopy(default_server)
    server.dataset_id = dataset_id
    server.protocol = "griddap"
    server.griddap_initialize()

    verbose_print(f"Selected '{dataset_id}' dataset.", verbose)
    verbose_print(f"Dataset info available at: {server.get_info_url()}", verbose)

    # Setting constraints that match. erddapy exposes ``_constraints_original``;
    # we merge user constraints on top of the dataset's full-range defaults.
    if constraints:
        original = getattr(server, "_constraints_original", None) or dict(
            server.constraints
        )
        merged = {**original, **constraints}
        for k, v in merged.items():
            if k in server.constraints.keys():
                server.constraints[k] = v
                if hasattr(server, "_constraints_original"):
                    server._constraints_original[k] = v

    # The same for variables
    if variables:
        server.variables = [v for v in server.variables if v in variables]
    verbose_print(
        f"Selected {len(server.variables)} variables: {server.variables}.", verbose
    )
    return server


def _get_griddap_dataset_url(
    dataset_id: str,
    variables: Optional[Container[str]] = None,
    constraints: Optional[Dict[str, Any]] = None,
    response: str = "nc",
    verbose: bool = False,
) -> str:
    """
    Get the URL for downloading a dataset using the Griddap protocol.

    Args:
        dataset_id (str): The ID of the dataset to download.
        variables (container of str, optional): Container of variable names to select.
        constraints (dict[str, Any], optional): Dictionary of constraints to apply.
        response (str, optional): The response format. Default is "nc".
        verbose (bool, optional): If True, detailed information will be printed.

    Returns:
        str: The URL for downloading the dataset.

    Example:
        url = _get_griddap_dataset_url("dataset123", variables=["temperature", "salinity"], constraints={"time": "2023-01-01"}, response="csv", verbose=True)
    """
    server = _build_griddap_server(dataset_id, variables, constraints, verbose)
    return server.get_download_url(response=response)


# Dimensions handled by ``build_constraints`` and reported by ``_layer_info``.
_DIMENSIONS = ("time", "latitude", "longitude", "depth")


@lru_cache(maxsize=32)
def _layer_info(dataset_id: str) -> Dict[str, Any]:
    """
    Fetch structured metadata for a single griddap layer.

    Args:
        dataset_id (str): The dataset ID.

    Returns:
        dict: A dictionary with keys:
            - ``dataset_id``
            - ``dimensions``: mapping dim name -> (min, max) for time/latitude/longitude/depth
            - ``variables``: mapping variable name -> {"units", "long_name"}
            - ``griddap_constraints``: the dataset's full-range constraints dict
    """
    server = _build_griddap_server(dataset_id)

    dimensions: Dict[str, Tuple[Any, Any]] = {}
    for dim in _DIMENSIONS:
        lo = server.constraints.get(f"{dim}>=")
        hi = server.constraints.get(f"{dim}<=")
        if lo is not None or hi is not None:
            dimensions[dim] = (lo, hi)

    variables: Dict[str, Dict[str, Optional[str]]] = {}
    try:
        info = pd.read_csv(server.get_info_url(response="csv"))
        attrs = info[info["Row Type"] == "attribute"]
        for var in server.variables:
            sub = attrs[attrs["Variable Name"] == var]
            units = sub.loc[sub["Attribute Name"] == "units", "Value"]
            long_name = sub.loc[sub["Attribute Name"] == "long_name", "Value"]
            variables[var] = {
                "units": units.iloc[0] if not units.empty else None,
                "long_name": long_name.iloc[0] if not long_name.empty else None,
            }
    except Exception:
        # Metadata is best-effort; fall back to bare variable names.
        for var in server.variables:
            variables[var] = {"units": None, "long_name": None}

    return {
        "dataset_id": dataset_id,
        "dimensions": dimensions,
        "variables": variables,
        "griddap_constraints": dict(server.constraints),
    }


def build_constraints(
    dataset_id: Optional[str] = None,
    time: Optional[Tuple[Any, Any]] = None,
    latitude: Optional[Tuple[float, float]] = None,
    longitude: Optional[Tuple[float, float]] = None,
    depth: Optional[Tuple[float, float]] = None,
    time_step: int = 1,
    latitude_step: int = 1,
    longitude_step: int = 1,
    depth_step: int = 1,
    validate: bool = True,
) -> Dict[str, Any]:
    """
    Build a griddap constraints dictionary from human-friendly bounds.

    Instead of hand-writing the ``{"time>=": ..., "time<=": ..., "time_step": ...}``
    dictionary, pass ``(min, max)`` tuples per dimension and optional strides.

    Args:
        dataset_id (str, optional): If given and ``validate`` is True, bounds are
            checked against the dataset's real dimension ranges and a warning is
            emitted (not an error) when they fall outside.
        time (tuple, optional): ``(start, end)`` as ISO strings, e.g. ("2000-01-01T00:00:00Z", "2010-01-01T00:00:00Z").
        latitude (tuple, optional): ``(min, max)`` latitude in degrees.
        longitude (tuple, optional): ``(min, max)`` longitude in degrees.
        depth (tuple, optional): ``(min, max)`` depth.
        time_step (int): Stride along time. Default 1.
        latitude_step (int): Stride along latitude. Default 1.
        longitude_step (int): Stride along longitude. Default 1.
        depth_step (int): Stride along depth. Default 1.
        validate (bool): If True and ``dataset_id`` is given, validate bounds.

    Returns:
        dict: A constraints dictionary suitable for ``download_layers`` / ``load_layer``.

    Example:
        constraints = build_constraints(
            time=("2000-01-01T00:00:00Z", "2010-01-01T00:00:00Z"),
            latitude=(0, 10),
            longitude=(0, 10),
        )
    """
    bounds = {
        "time": (time, time_step),
        "latitude": (latitude, latitude_step),
        "longitude": (longitude, longitude_step),
        "depth": (depth, depth_step),
    }

    real_ranges: Dict[str, Tuple[Any, Any]] = {}
    if validate and dataset_id is not None:
        try:
            real_ranges = _layer_info(dataset_id)["dimensions"]
        except Exception as exc:  # network/validation is best-effort
            warnings.warn(
                f"Could not fetch ranges for '{dataset_id}' to validate constraints: {exc}"
            )

    constraints: Dict[str, Any] = {}
    for dim, (value, step) in bounds.items():
        if value is None:
            continue
        lo, hi = value
        constraints[f"{dim}>="] = lo
        constraints[f"{dim}<="] = hi
        constraints[f"{dim}_step"] = step

        if dim in real_ranges:
            rlo, rhi = real_ranges[dim]
            # Numeric dimensions only; skip time string comparisons.
            if dim != "time" and None not in (rlo, rhi):
                try:
                    if lo < rlo or hi > rhi:
                        warnings.warn(
                            f"Requested {dim} range ({lo}, {hi}) is outside the "
                            f"dataset range ({rlo}, {rhi}) for '{dataset_id}'."
                        )
                except TypeError:
                    pass

    return constraints


@lru_cache(2)
def _layer_dataframe(include_allDatasets: bool = False) -> pd.DataFrame:
    """
    Requests the list of layers as a pandas DataFrame.

    Args:
        include_allDatasets (bool): Whether to include the row with the 'allDatasets' dataset.

    Returns:
        pd.DataFrame: DataFrame containing the list of layers.
    """
    s = deepcopy(default_server)
    s.dataset_id = "allDatasets"
    s.protocol = "tabledap"
    df = s.to_pandas()

    if not include_allDatasets:
        df = df.iloc[1:]
    return df


def _download_layer(
    dataset_id: str,
    output_directory: Optional[Union[str, Path]] = None,
    response: str = "nc",
    constraints: Optional[Dict[str, Any]] = None,
    skip_confirmation: Optional[bool] = None,
    verbose: bool = True,
    log: bool = True,
    timestamp: bool = True,
    timeout: int = 120,
    variables: Optional[Container[str]] = None,
    **httpx_kwargs,
) -> None:
    """
    Downloads a dataset layer.

    Args:
        dataset_id (str): Dataset ID to download.
        output_directory (str or Path, optional): Directory where downloaded files will be saved. If not provided, the default directory will be used.
        response (str, optional): Format of the response to download. Default is "nc".
        constraints (dict, optional): Constraints to apply to the downloaded data.
        skip_confirmation (bool, optional): If True, confirmation prompts will be skipped. If None, the value from the configuration will be used.
        verbose (bool, optional): If True, detailed information will be printed during the download process.
        log (bool, optional): If True, a log of the download will be created.
        timestamp (bool, optional): If True, a timestamp will be added to the downloaded files' names.
        timeout (int, optional): Timeout in seconds for the download request.
        httpx_kwargs: keyword arguments for the httpx.stream function.

    Returns:
        None
    """
    _timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    filename = (
        f"{dataset_id}_{_timestamp}.{response}"
        if timestamp
        else f"{dataset_id}.{response}"
    )
    outdir = (
        Path(output_directory) if output_directory else Path(config["data_directory"])
    )
    local_path = outdir.joinpath(filename)

    # Check for existing layers
    if skip_confirmation is None:
        skip_confirmation = _as_bool(config["skip_confirmation"])
    if not skip_confirmation:
        print()
        print(f"Data directory is '{outdir}'.", end="\n\n")
        existing_layers = [
            i
            for i in outdir.iterdir()
            if str(i.name).startswith(dataset_id) and not str(i.name).endswith(".log")
        ]
        if existing_layers:
            print(
                f"You have {len(existing_layers)} local datasets with the same prefix as '{dataset_id}' in the data directory:"
            )
            for layer in existing_layers:
                print(layer.name, "\t", convert_bytes(layer.stat().st_size))
            print()
            print("You can check it again by running `list_local_data()`.")
            print(
                "To check the constraints of each existing dataset, see the log files in the data directory.",
                end="\n\n",
            )

            msg = ""
            if not confirm(msg):
                return

    # Configure logging
    logfile = local_path.with_suffix(".log")
    logging.basicConfig(
        filename=logfile,
        format="%(asctime)s %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H%M%S",
    )

    msg = f"Downloading dataset '{dataset_id}' as {response} file to '{outdir}'."
    info_logger(msg, log)
    verbose_print(msg, verbose)

    msg = "Constraints are:"
    info_logger(msg, log)
    verbose_print(msg, verbose)
    info_logger(constraints, log)
    verbose_print(constraints, verbose)

    url = _get_griddap_dataset_url(
        dataset_id, variables=variables, constraints=constraints, response=response
    )
    _download_file_from_url(url, local_path, timeout=timeout, **httpx_kwargs)
    if (verbose or log) and local_path.exists():
        filesize = convert_bytes(local_path.stat().st_size)
        msg = f"Download finished at '{local_path}'. File size is {filesize}."
        info_logger(msg, log)
        verbose_print(msg, verbose)
