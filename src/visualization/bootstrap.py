"""Descarga los resultados reproducibles cuando el servidor no los tiene."""

import hashlib
import tempfile
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from src.config import PROCESSED

URL = "https://github.com/TaniaRmz/Practica5AyMD/releases/download/dashboard-data-v1/dashboard-data-v1.zip"
SHA256 = "90e842f2f536d844669f71234fc5d415c1b0aa6f787160861e3b3eaaea5560d3"
FILES = ("prepared.parquet", "results.json", "correlation.csv", "variance.csv",
         "weights.csv", "projection.parquet", "hallazgos.md")


def ensure_processed(folder=PROCESSED):
    if all((folder / name).is_file() for name in FILES):
        return
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        archive = Path(temp) / "data.zip"
        digest = hashlib.sha256()
        with urlopen(URL, timeout=120) as response, archive.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != SHA256:
            raise ValueError("La descarga de datos no coincide con la versión publicada.")
        with ZipFile(archive) as bundle:
            for name in FILES:
                target = folder / name
                if target.exists():
                    continue
                temporary = target.with_suffix(target.suffix + ".download")
                with bundle.open(name) as source, temporary.open("wb") as output:
                    while chunk := source.read(1024 * 1024):
                        output.write(chunk)
                temporary.replace(target)
