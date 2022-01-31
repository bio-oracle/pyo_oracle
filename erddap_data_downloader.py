"""
Batch download of multiple Bio-ORACLE ERDDAP datasets.
"""

import argparse
import requests
from erddapy import ERDDAP


def download_file(url, local_filename=None, directory="./"):
    """
    Downloads a large file from a URL.
    From: https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    """
    if not local_filename:
        local_filename = url.split("/")[-1].split("?")[0]

    if directory:
        local_filename = directory + local_filename

    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        print(f"Writing to '{local_filename}'.\n")
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return local_filename


def download_griddap_dataset(
    erddap_server,
    dataset,
    variables,
    constraints,
    response="nc",
    directory="./",
    _print=True,
):
    """
    Downloads dataset based on constraints and variables.
    """
    printer = lambda message: print(message) if _print else None

    erddap_server.dataset_id = dataset
    erddap_server.griddap_initialize()

    printer(f"Selected '{dataset}' dataset.")
    printer(f"Dataset info available at: {erddap_server.get_info_url()}")

    # Setting constraints that match
    for k, v in constraints.items():
        if k in erddap_server.constraints.keys():
            erddap_server.constraints[k] = v

    # The same for variables
    erddap_server.variables = [v for v in erddap_server.variables if v in variables]
    printer(
        f"Selected {len(erddap_server.variables)} variables: {erddap_server.variables}."
    )
    url = erddap_server.get_download_url(response=response)
    download_file(url, directory=directory)


def main(
    server_url,
    datasets,
    variables,
    constraints,
    response,
    directory,
    _print=True,
):
    if _print:
        print(f"Connecting to server at: '{server_url}'.\n")
    erddap_server = ERDDAP(server=server_url, protocol="griddap")
    for dataset in datasets:
        download_griddap_dataset(
            erddap_server, dataset, variables, constraints, response, directory
        )


if __name__ == "__main__":
    usage = """
    python erddap_data_downloader.py \n \
           -s https://erddap-test.emodnet.eu/erddap/ \n \
           -d biooracle_sea_temp,biooracle4_15e4_aeaf_2ae3 \n \
           -v tempmax,tempmin,thetao_max,thetao_min \n \
           -c \"{'time>=': '2000-01-01T00:00:00Z',\n\t\t'time<=': '2014-01-01T00:00:00Z',\n\t\t'latitude>=': 50.0,\n\t\t'latitude<=': 50.5,\n\t\t'longitude>=': 5.1,\n\t\t'longitude<=': 6.0}\" \n \
           -o data/
           """

    parser = argparse.ArgumentParser(
        description="Download multiple datasets based on selected variables and constraints.",
        usage=usage,
    )
    parser.add_argument(
        "-s",
        "--server",
        help="URL of the ERDDAP server.",
        default="https://erddap-test.emodnet.eu/erddap/",
    )
    parser.add_argument(
        "-d",
        "--datasets",
        help="Datasets to be queried and downloaded, comma separated. "
        "Example: 'biooracle_sea_temp,biooracle4_15e4_aeaf_2ae3'",
    )
    parser.add_argument(
        "-v",
        "--variables",
        help="Variables to be selected and downloaded, comma separated. "
        "Download will only be attempted if variables are present in the dataset. "
        "Example: 'tempmax,tempmin,thetao_max,thetao_min'",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--constraints",
        help="Constraints to be applied to the dataset, comma separated. "
        "These are usually dimensions such as latitude, longitude, time. "
        "Should be passed as a string representing a dictionary. "
        "The easiest way to do that is to build the dictionary and then display it with the str() function. "
        "For an example, see the usage prompt.",
    )
    parser.add_argument(
        "-r",
        "--response",
        help="Type of response returned from the request. "
        "Choose between different formats available from ERDDAP: html, htmlTable, csv, nc, ...",
        default="nc",
    )
    parser.add_argument(
        "-o",
        "--output_directory",
        help="Output directory to dump the data.",
        default="./",
    )
    args = parser.parse_args()
    datasets = args.datasets.split(",")
    variables = args.variables.split(",")
    constraints = eval(args.constraints)
    main(
        server_url=args.server,
        datasets=datasets,
        variables=variables,
        constraints=constraints,
        response=args.response,
        directory=args.output_directory,
    )
