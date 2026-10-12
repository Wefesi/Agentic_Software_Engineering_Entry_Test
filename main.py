from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests


PYPI_JSON_URL = "https://pypi.org/pypi"
REQUEST_TIMEOUT = 15


def pypi_json(session, package, version=None):
    package_path = quote(package, safe="")
    url = f"{PYPI_JSON_URL}/{package_path}"
    if version is not None:
        url += f"/{quote(version, safe='')}"
    url += "/json"

    response = session.get(url, timeout=REQUEST_TIMEOUT)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def main():
    requirements_path = Path(__file__).with_name("requirements.txt")
    requirements = [
        line.split("==")
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
    ]
    session = requests.Session()

    project_cache = {}
    packages_not_on_pypi = 0
    versions_not_on_pypi = 0
    oldest_release = None

    for package, version in requirements:
        if package not in project_cache:
            project_cache[package] = pypi_json(session, package)
        project = project_cache[package]

        if project is None:
            packages_not_on_pypi += 1
            continue

        release_data = pypi_json(session, package, version)
        if release_data is None:
            versions_not_on_pypi += 1
            continue

        urls = release_data.get("urls", [])
        if not urls:
            continue
        upload_time = urls[0].get("upload_time")
        if not upload_time:
            continue

        uploaded_at = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
        if oldest_release is None or uploaded_at < oldest_release[0]:
            oldest_release = (uploaded_at, f"{package}=={version}")

    print(f"Dependencies checked: {len(requirements)}")
    print(f"Packages not on PyPI: {packages_not_on_pypi}")
    print(f"Versions not on PyPI: {versions_not_on_pypi}")
    oldest = oldest_release[1] if oldest_release is not None else "None"
    print(f"Oldest pinned release: {oldest}")


if __name__ == "__main__":
    main()