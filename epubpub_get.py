# -*- coding: utf-8 -*-
__version__ = "0.04.0"
"""
Source : https://github.com/izneo-get/epubpub-get

Script pour sauvegarder les livres de epub.pub
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from bs4 import BeautifulSoup
#import urllib.parse
import os
import re
import sys
#import zipfile
import shutil


def requests_retry_session(
    retries=5,
    backoff_factor=1,
    status_forcelist=(401, 402, 403, 404, 500, 502, 504),
    session=None,
):
    """Permet de gérer les cas simples de problèmes de connexions."""
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def check_version():
    latest_version_url = 'https://raw.githubusercontent.com/izneo-get/epubpub-get/master/VERSION'
    res = requests.get(latest_version_url)
    if res.status_code != 200:
        print(f"Version {__version__} (impossible de vérifier s'il existe une version plus récente)")
    else:
        latest_version = res.text.strip()
        if latest_version == __version__:
            print(f"Version {__version__} (la plus récente)")
        else:
            print(f"Version {__version__} (il existe une version plus récente : {latest_version})")

if __name__ == "__main__":
    base_url_to_remove = (
        "https://asset.epub.pub/epub/"  # La partie à supprimer pour l'arborescence.
    )
    output_folder = "DOWNLOADS"

    check_version()

    # Récupération de l'URL du livre souhaité (si pas en argument, on le demande).
    requested_url = ""
    if len(sys.argv) > 1:
        requested_url = sys.argv[1]
    while requested_url.upper() != "Q" and not re.match(
        "https://www.epub.pub/book/(.+)", requested_url
    ):
        requested_url = input(
            'URL de la publication au format "https://www.epub.pub/book/{title}" ("Q" pour quitter) : '
        )

    if requested_url.upper() == "Q":
        sys.exit()

    # Téléchargement de la page.
    response = requests_retry_session().get(requested_url)
    if response.status_code != 200:
        print("URL introuvable")
        os.system("pause")
        sys.exit()

    # On trouve l'URL de la page de lecture en ligne.
    soup = BeautifulSoup(response.text, "html.parser")
    asset = soup.find(title="Read Online(Continuous version)")
    id = asset.attrs["data-readid"]
    url_download = f"https://continuous.epub.pub/epub/{id}"
    response = requests_retry_session().get(url_download)
    if response.status_code != 200:
        print("URL introuvable")
        os.system("pause")
        sys.exit()

    # On trouve l'URL de la page qui contient toutes les références (normalement, "content.opf").
    soup = BeautifulSoup(response.text, "html.parser")
    asset = soup.find(id="assetUrl")
    url = asset.attrs["value"]

    url_base = "/".join(url.split("/")[0:-1]) + "/"

    print(url, end="")
    try:
        response = requests_retry_session().get(url)
    except:
        print(" ERREUR : impossible de récupérer le fichier (404)")
        os.system("pause")
        sys.exit()
    print(" OK")

    remove_sponsor = True

    total_errors = 0
    if response.status_code != 200:
        print("Format inattendu...")
        os.system("pause")
        sys.exit()

    # Création du répertoire de destination.
    file_name = url.replace(base_url_to_remove, "")
    os.makedirs(os.path.dirname(output_folder + "/" + file_name), exist_ok=True)

    with open(output_folder + "/" + file_name, "wb") as f:
        f.write(response.content)
    soup = BeautifulSoup(response.text, "html.parser")

    # On boucle sur tous les "item" qui composent le livre.
    elems = soup.find_all("item")

    for e in elems:
        file_name = e.attrs["href"]
        src = url_base + file_name
        print(src, end="")
        try:
            response = requests_retry_session().get(src)
        except:
            print(" ERREUR : impossible de récupérer le fichier (404)")
            os.system("pause")
            sys.exit()

        if response.status_code == 200:
            print(" OK")
            # Création du répertoire de destination.
            file_name = src.replace(base_url_to_remove, "")
            os.makedirs(os.path.dirname(output_folder + "/" + file_name), exist_ok=True)
            to_write = response.content
            if remove_sponsor and file_name.split(".")[-1].lower() in (
                "html",
                "htm",
                "xhtml",
            ):
                to_write = re.sub(
                    r"<div id=\"sponsor\">(.+?)</div>", "", response.text
                ).encode()
            with open(output_folder + "/" + file_name, "wb") as f:
                f.write(to_write)

        else:
            print(f" Erreur {response.status_code}")
            total_errors = total_errors + 1

    # On récupère en plus les fichiers supplémentaires.
    for e in ["mimetype", "META-INF/container.xml"]:
        file_name = e
        new_url_base = url_base.split(".epub/")[0] + ".epub/"
        src = new_url_base + file_name
        print(src, end="")
        try:
            response = requests_retry_session().get(src)
        except:
            print(" ERREUR : impossible de récupérer le fichier (404)")
            os.system("pause")
            sys.exit()
        if response.status_code == 200:
            print(" OK")
            # Création du répertoire de destination.
            file_name = src.replace(base_url_to_remove, "")
            os.makedirs(os.path.dirname(output_folder + "/" + file_name), exist_ok=True)
            to_write = response.content
            if remove_sponsor and file_name.split(".")[-1].lower() in (
                "html",
                "htm",
                "xhtml",
            ):
                to_write = re.sub(
                    r"<div id=\"sponsor\">(.+?)</div>", "", response.text
                ).encode()
            with open(output_folder + "/" + file_name, "wb") as f:
                f.write(to_write)

        else:
            print(f" Erreur {response.status_code}")
            total_errors = total_errors + 1

    epub_name = url_base.split(".epub/")[0].replace(base_url_to_remove, "") + ".epub"

    # On vérifie si le fichier epub existe.
    if os.path.isfile(output_folder + "/" + epub_name):
        print(
            "Problème : le fichier '"
            + output_folder
            + "/"
            + epub_name
            + "' existe déjà."
        )
        print("On s'arrête là. Les fichiers temporaires sont conservés mais aucun epub n'a été compilé.")
    else:
        if total_errors == 0:
            print("Création de l'ePub", end="")
            shutil.make_archive(
                output_folder + "/" + epub_name, "zip", output_folder + "/" + epub_name
            )
            shutil.rmtree(output_folder + "/" + epub_name)
            os.rename(
                output_folder + "/" + epub_name + ".zip",
                output_folder + "/" + epub_name,
            )
            print(" OK")
        else:
            print(
                f"Il y a eu {total_errors} erreur(s). Les fichiers temporaires sont conservés mais aucun epub n'a été compilé."
            )

    # Pause pour que l'utilisateur ait le temps de lire la sortie.
    os.system("pause")