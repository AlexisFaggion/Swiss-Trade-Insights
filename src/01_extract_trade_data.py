from pathlib import Path
import zipfile

import requests


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "https://ckan.opendata.swiss/api/3/action/package_show"

DATASET_ID = "waren-aussenhandel-nach-verwendungszweck-land"

RESOURCE_NAME = "VZ_IMPEXP_DEF"

CHUNK_SIZE = 1024 * 1024  # 1 MiB


# ============================================================
# PROJECT PATHS
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

ZIP_PATH = RAW_DATA_DIR / "VZ_IMPEXP_DEF.zip"


# ============================================================
# FUNCTIONS
# ============================================================

def get_dataset_metadata():
    """Retrieve dataset metadata from the opendata.swiss CKAN API."""

    print("Connecting to opendata.swiss API...")

    try:
        response = requests.get(
            API_URL,
            params={"id": DATASET_ID},
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

    except requests.exceptions.Timeout as e:
        raise RuntimeError("API request timed out.") from e

    except requests.exceptions.ConnectionError as e:
        raise RuntimeError("Unable to connect to the API.") from e

    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"API returned HTTP error: {e}") from e

    except requests.exceptions.JSONDecodeError as e:
        raise RuntimeError("API returned an invalid JSON response.") from e

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Unexpected API request error: {e}") from e

    # Check the API-level success flag, independently of HTTP status.
    if not data.get("success"):
        raise RuntimeError("The API returned success=False.")

    print("Dataset metadata retrieved successfully.")

    return data["result"]


def find_resource(dataset):
    """
    Find the required resource in the dataset metadata.

    Args:
        dataset (dict): Metadata returned by the CKAN API.
        
    Returns:
        dict: Metadata of the matching resource.
    """

    print(f"Searching for resource: {RESOURCE_NAME}...")

    resources = dataset.get("resources", [])

    if not isinstance(resources, list):
        raise ValueError("Invalid API response: 'resources' must be a list.")

    for resource in resources:
        if not isinstance(resource, dict):
            continue

        names = resource.get("name", {})

        # Support both multilingual name dictionaries and strings.
        if isinstance(names, dict):
            resource_names = names.values()
        elif isinstance(names, str):
            resource_names = [names]
        else:
            continue

        if RESOURCE_NAME in resource_names:
            print(f"Resource found: {RESOURCE_NAME}")
            return resource

    raise ValueError(
        f"Resource '{RESOURCE_NAME}' not found "
        f"among {len(resources)} available resources."
    )


def build_download_url(resource):
    """
    Convert the public Nextcloud share URL
    into a direct download URL.

    Args:
        resource (dict): Metadata of the selected resource.

    Returns:
        str: Direct download URL.
    """

    share_url = resource.get("download_url")

    if not share_url:
        raise ValueError("No download URL found for the resource.")
    
    share_url = share_url.rstrip("/")

    direct_url = f"{share_url}/download"

    print("Direct download URL created.")

    return direct_url


def download_zip(download_url):
    """
    Download and validate the ZIP archive.

    Use a temporary file to avoid retaining incomplete downloads.
    Skip downloading when an existing valid ZIP is found.

    Args:
        download_url (str): Direct URL of the ZIP archive.
    """

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Check the ZIP structure, but not the integrity of its contents.
    # Existing files are reused without checking for dataset updates.
    # A future automated pipeline should validate integrity and freshness.      

    # Avoid downloading the dataset again if a valid ZIP exists.
    if ZIP_PATH.exists():
        if zipfile.is_zipfile(ZIP_PATH):
            print(f"ZIP already exists: {ZIP_PATH.name}")
            return

        print("Existing ZIP is invalid. Downloading again.")

    # Keep incomplete downloads separate from the final ZIP file.
    temp_path = ZIP_PATH.with_suffix(".zip.part")

    print("Downloading dataset...")

    try:
        # Stream the response instead of loading the entire archive.
        with requests.get(download_url, stream=True, timeout=300) as response:
            response.raise_for_status()

            total_bytes = 0

            with open(temp_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        file.write(chunk)
                        total_bytes += len(chunk)

                        # Display download progress in MiB
                        total_mib = total_bytes / 1024 / 1024

                        print(f"\rDownloaded: {total_mib:.1f} MiB", end="")

        print()

        # Confirm the downloaded file has a valid ZIP structure.
        if not zipfile.is_zipfile(temp_path):
            raise ValueError("Downloaded file is not a valid ZIP archive.")

        # Make the final ZIP available only after validation.
        temp_path.replace(ZIP_PATH)

        print(f"Download completed: {ZIP_PATH}")

    except (requests.exceptions.RequestException, OSError, ValueError):
        # Remove partial downloads and preserve the original error.
        temp_path.unlink(missing_ok=True)
        raise


def inspect_zip():
    """
    Inspect the ZIP archive without extracting its contents.

    Display the number of files and their compressed
    and uncompressed sizes.
    """

    print()
    print("Inspecting ZIP archive...")

    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"{ZIP_PATH} does not exist.")

    if not zipfile.is_zipfile(ZIP_PATH):
        raise ValueError("The downloaded file is not a valid ZIP archive.")

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        # Retrieve file metadata without extracting the archive.
        files = archive.infolist()

        print(f"Number of files in archive: {len(files)}")

        for file_info in files:
            compressed_mib = file_info.compress_size/ 1024/ 1024

            uncompressed_mib = file_info.file_size/ 1024/ 1024

            print()
            print(f"File: {file_info.filename}")
            print(f"Compressed size: {compressed_mib:.2f} MiB")
            print(f"Uncompressed size: {uncompressed_mib:.2f} MiB")


# ============================================================
# MAIN 
# ============================================================

def main():

    print("=" * 60)
    print("SWISS TRADE DATA - EXTRACTION PIPELINE")
    print("=" * 60)

    # Retrieve metadata and identify the definitive data resource.
    dataset = get_dataset_metadata()

    print(f"Dataset: {dataset.get('name')}")
    print(f"Last modified: {dataset.get('metadata_modified')}")

    resource = find_resource(dataset)

    # Build the download URL, save the archive and inspect its files.
    download_url = build_download_url(resource)

    download_zip(download_url)

    inspect_zip()

    print()
    print("=" * 60)
    print("EXTRACTION COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()