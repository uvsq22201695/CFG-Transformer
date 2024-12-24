import argparse

from grammaire import lire
import os


def main():
    """
    Fonction principale pour lancer la transformation de grammaire.
    """

    # Analyse des arguments
    parser = argparse.ArgumentParser(description="Générer les mots d'une longueur donnée.")
    parser.add_argument("longueur", type=int, help="Longueur des mots à générer.")
    parser.add_argument("file", type=str, help="Chemin du fichier contenant la grammaire.")
    args = parser.parse_args()

    # Fichier d'entrée
    fichier = args.file
    if not os.path.isfile(fichier):
        print(f"Erreur : Le fichier '{fichier}' n'existe pas.")
        return

    # 1) Lire la grammaire
    grammaire_obj = lire(fichier)

    # 2) Générer les mots
    mots = grammaire_obj.generer_mots(args.longueur)

    # 3) Afficher les mots
    for mot in mots:
        print(mot)

if __name__ == "__main__":
    main()