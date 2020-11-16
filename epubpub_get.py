# -*- coding: utf-8 -*-
__version__ = "0.01.0"
"""
Source : https://github.com/izneo-get/epubpub-get

Script pour sauvegarder les livres de epub.pub
"""
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
import re
import sys
import zipfile
import shutil

if __name__ == "__main__":

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

    response = requests.request("GET", requested_url)
    if response.status_code != 200:
        print("URL introuvable")
        sys.exit()
    soup = BeautifulSoup(response.text, "html.parser")
    asset = soup.find(title="Read Online(Continuous version)")
    id = asset.attrs["data-readid"]
    url_download = f"https://continuous.epub.pub/epub/{id}"
    response = requests.request("GET", url_download)
    if response.status_code != 200:
        print("URL introuvable")
        sys.exit()

    soup = BeautifulSoup(response.text, "html.parser")
    asset = soup.find(id="assetUrl")
    url = asset.attrs["value"]

    url_base = "/".join(url.split("/")[0:-1]) + "/"

    response = requests.request("GET", url)

    output_folder = "DOWNLOADS"
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    output_folder = output_folder + "/" + requested_url.split("/")[-1]
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    remove_sponsor = True

    total_errors = 0
    if response.status_code != 200:
        print("Format inattendu...")
        sys.exit()
        
    with open(output_folder + "/content.opf", "wb") as f:
        f.write(response.content)
    soup = BeautifulSoup(response.text, "html.parser")

    elems = soup.find_all("item")

    for e in elems:
        file_name = e.attrs["href"]
        src = url_base + file_name
        print(src, end="")
        response = requests.request("GET", src)
        if response.status_code == 200:
            print(" OK")
            # Création du répertoire de destination.
            folders = file_name.split("/")
            mid_path = ""
            for elem in folders[:-1]:
                mid_path += elem
                if not os.path.exists(output_folder + "/" + mid_path):
                    os.mkdir(output_folder + "/" + mid_path)
                mid_path += "/"

            to_write = response.content
            if remove_sponsor and file_name.split(".")[-1].lower() in (
                "html",
                "htm",
                "xhtml"
            ):
                to_write = re.sub(
                    r"<div id=\"sponsor\">(.+?)</div>", "", response.text
                ).encode()
            with open(output_folder + "/" + file_name, "wb") as f:
                f.write(to_write)

        else:
            print(f" Erreur {response.status_code}")
            total_errors = total_errors + 1

    for e in ["mimetype", "META-INF/container.xml"]:
        file_name = e
        new_url_base = url_base.split(".epub/")[0] + '.epub/'
        src = new_url_base + file_name
        print(src, end="")
        response = requests.request("GET", src)
        if response.status_code == 200:
            print(" OK")
            # Création du répertoire de destination.
            folders = file_name.split("/")
            mid_path = ""
            for elem in folders[:-1]:
                mid_path += elem
                if not os.path.exists(output_folder + "/" + mid_path):
                    os.mkdir(output_folder + "/" + mid_path)
                mid_path += "/"

            to_write = response.content
            if remove_sponsor and file_name.split(".")[-1].lower() in (
                "html",
                "htm",
            ):
                to_write = re.sub(
                    r"<div id=\"sponsor\">(.+?)</div>", "", response.text
                ).encode()
            with open(output_folder + "/" + file_name, "wb") as f:
                f.write(to_write)

        else:
            print(f" Erreur {response.status_code}")
            total_errors = total_errors + 1

    if os.path.isfile(output_folder + ".epub"):
        print("Problème : '" + output_folder + ".epub' existe déjà.")
        print("On s'arrête là.")
    else:
        print("Création de l'ePub")
        shutil.make_archive(output_folder, "zip", output_folder)
        os.rename(output_folder + ".zip", output_folder + ".epub")
        if total_errors == 0:
            shutil.rmtree(output_folder)
        else:
            print(f"Il y a eu {total_errors} erreurs.")