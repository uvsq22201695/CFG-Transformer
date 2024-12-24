#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import copy
import os

from outil_grammaire import ecrire, lire


def main():
    """
    Fonction principale pour lancer la transformation de grammaire.
    """

    # Analyse des arguments
    parser = argparse.ArgumentParser(description="Transformation de grammaire contextuelle.")
    parser.add_argument("file", type=str, help="Chemin du fichier contenant la grammaire.")
    args = parser.parse_args()

    # Fichier d'entrée
    fichier = args.file
    if not os.path.isfile(fichier):
        print(f"Erreur : Le fichier '{fichier}' n'existe pas.")
        return

    # 1) Lire la grammaire
    grammaire_obj = lire(fichier)

    # 2) a. Transformer en CNF
    cnf = copy.deepcopy(grammaire_obj)
    cnf.convertir_en_forme_normale_de_Chomsky()

    # 2) b. Transformer en GNF
    gbh = copy.deepcopy(grammaire_obj)
    gbh.convertir_en_forme_normale_de_Greibach()

    # 3) Exporter
    ecrire(cnf, fichier, extension="chomsky")
    ecrire(gbh, fichier, extension="greibach")


if __name__ == "__main__":
    main()
