class Grammaire:
    def __init__(self):
        """
        Initialise la structure de données pour une grammaire algébrique.
        """
        self.axiome = "S"
        self.non_terminaux = set(self.axiome)
        self.terminaux = set()
        self.regles = {}


    def lire(self, fichier: str):
        """
        Lit une grammaire algébrique à partir d'un fichier texte.
        """

        if not self._fichier_a_extension_valide(fichier):
            raise ValueError("Le fichier doit avoir l'extension « .general ».")

        with open(fichier, 'r') as f:
            for ligne in f:
                self._traiter_ligne(ligne)

    @staticmethod
    def _fichier_a_extension_valide(fichier: str) -> bool:
        """
        Vérifie que le fichier a l'extension correcte.
        :param fichier: Chemin du fichier.
        :return: True si l'extension est valide, False sinon.
        """
        return fichier.endswith(".general")

    def _traiter_ligne(self, ligne: str):
        """
        Analyse une ligne contenant une règle de grammaire et l'ajoute.
        :param ligne: Ligne de texte représentant une règle.
        """
        if not ligne:  # Ignorer les lignes vides
            return

        try:
            membre_gauche, membre_droit = map(str.strip, ligne.split(":"))
        except ValueError:
            raise ValueError(f"Ligne mal formatée : {ligne}")

        self._valider_non_terminal(membre_gauche)
        self.non_terminaux.add(membre_gauche)

        produits = membre_droit.split("|")
        for produit in produits:
            self._analyser_produit(membre_gauche, produit.replace(" ", ""))

    def _valider_non_terminal(self, non_terminal: str):
        """
        Vérifie si le membre gauche est un non-terminal valide.
        :param non_terminal: Symbole non-terminal.
        """
        if non_terminal == self.axiome:
            return

        if (len(non_terminal) < 2 or not non_terminal[0].isupper() or non_terminal[0] == "E"
                or not non_terminal[1].isdigit()):
            raise ValueError(f"Non-terminal invalide : {non_terminal}")

    def _analyser_produit(self, membre_gauche: str, produit: str):
        """
        Analyse et ajoute un produit à une règle.
        :param membre_gauche: Non-terminal associé à la règle.
        :param produit: Production à analyser.
        """
        index = 0
        while index < len(produit):
            if index + 1 < len(produit) and produit[index].isupper() and produit[index + 1].isdigit():
                # Non-terminal
                non_terminal = produit[index:index + 2]
                self.non_terminaux.add(non_terminal)
                index += 2
            elif produit[index].islower():
                # Terminal
                self.terminaux.add(produit[index])
                index += 1
            elif produit[index] == "E":  # Epsilon
                index += 1
            else:
                raise ValueError(f"Symbole invalide dans '{produit}' pour '{membre_gauche}'.")

        self.regles.setdefault(membre_gauche, []).append(produit)


    def __repr__(self):
            """
            Représentation textuelle de la grammaire.
            """
            regles_str = "\n".join(
                f"{nt} -> {' | '.join(productions)}" for nt, productions in self.regles.items()
            )

            return f"Non-terminaux: {self.non_terminaux}\n" \
                   f"Terminaux: {self.terminaux}\n" \
                   f"Axiome: {self.axiome}\n" \
                   f"Règles:\n{regles_str}"


if __name__ == "__main__":
    grammaire = Grammaire()
    grammaire.lire("test.general")
    print(grammaire)