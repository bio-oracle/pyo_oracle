import httpx


default_server = ERDDAP(
    server=config["erddap_server"],
)


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
        constraints = {**server._constraints_original, **constraints}
        for k, v in constraints.items():
            if k in server.constraints.keys():
                server.constraints[k] = v
                server._constraints_original[k] = v

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

