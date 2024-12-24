import copy
from functools import lru_cache
from typing import Set

from analyseur_lexical import AnalyseurLexical

LETTRES = "ABCDFGHIJKLMNOPQRSTUVWXYZ"
CHIFFRES = "0123456789"

def generer_non_terminal(non_terminaux: Set[str]) -> str:
    """
    Génère un nouveau non-terminal unique.
    """
    for lettre in LETTRES:
        for chiffre in CHIFFRES:
            nouveau = f"{lettre}{chiffre}"
            if nouveau not in non_terminaux:
                return nouveau

    raise RuntimeError("Impossible de générer un nouveau non-terminal.")


class Grammaire:
    """
    Classe pour stocker une grammaire et effectuer des transformations en
    Forme Normale de Chomsky (CNF) ou de Greibach (GNF).
    """

    def __init__(self):
        self.regles_de_production = {}
        self.non_terminaux: Set[str] = set()
        self.axiome: str | None = None

    # Gestion des axiomes et des règles de production
    def set_axiome(self, axiome: str) -> None:
        """
        Met à jour l'axiome actuel et l'ajoute à l'ensemble des symboles non terminaux. Cette méthode
        est utilisée pour modifier le symbole principal du système et garantit que le nouvel axiome est
        suivi parmi les symboles non terminaux.

        :param axiome: Le nouvel axiome à définir.
        """
        self.axiome = axiome
        self.non_terminaux.add(axiome)

    def ajouter_regle(self, non_terminal_gauche: str, productions_associees: list) -> None:
        """
        Ajoute une règle de production à la grammaire. Si le non-terminal de gauche n'existe pas encore,
        il est ajouté à l'ensemble des non-terminaux. Les règles de production sont stockées sous forme de
        listes de tuples, où chaque tuple représente un symbole (non-terminal ou terminal).

        :param non_terminal_gauche: Le non-terminal de gauche de la règle.
        :param productions_associees: Les productions associées à ce non-terminal.
        """
        if non_terminal_gauche not in self.regles_de_production:
            self.regles_de_production[non_terminal_gauche] = []
        self.regles_de_production[non_terminal_gauche].extend(productions_associees)
        self.non_terminaux.add(non_terminal_gauche)

    # Transformations principales
    def convertir_en_forme_normale_de_Chomsky(self) -> None:
        """
        Transforme la grammaire en Forme Normale de Chomsky (CNF).
        Cette transformation suit les étapes suivantes dans l'ordre :
         – START : Introduction d'un nouvel axiome.
         – TERM : Remplacement des terminaux dans des productions de longueurs > 1.
         – BIN : Binarisation des productions pour qu'elles contiennent au maximum deux symboles.
         – DEL : Suppression des Epsilons-productions (productions générant des chaînes vides).
         – UNIT : Remplacement des règles unitaires de type X → Y par leurs expansions.

        À la fin, la grammaire respecte les contraintes de la Forme Normale de Chomsky.
        """

        self._introduire_axiome_depart()  # START
        self._remplacer_terminaux_dans_productions()  # TERM
        self._binariser_productions()  # BIN
        self._supprimer_productions_epsilon()  # DEL
        self._eliminer_regles_unitaires()  # UNIT

    def convertir_en_forme_normale_de_Greibach(self) -> None:
        """
        Transforme la grammaire en Forme Normale de Greibach (GNF).
        Étapes réalisées dans cet ordre :
         – DEL : Suppression des Epsilons-productions (productions générant des chaînes vides).
         – UNIT : Remplacement des règles unitaires de type X → Y par leurs expansions.
         – SUPPRIMER_RECURSIVITE_GAUCHE : Élimination de toute récursivité gauche.
         – TERM : Gestion des terminaux dans les productions (approche spécifique pour la GNF).
         – DÉCOMPOSER_LONGUES_PRODUCTIONS : Transformation des productions longues en successions intermédiaires.

        La GNF garantit que chaque production commence par un terminal, suivi éventuellement de non-terminaux.
        """
        self._supprimer_productions_epsilon()  # DEL
        self._eliminer_regles_unitaires()  # UNIT
        self._eliminer_recursivite_gauche()  # SUPPRIMER_RECURSIVITE_GAUCHE
        self._supprimer_productions_epsilon()  # DEL (encore une fois)
        self._remplacer_terminaux_dans_productions(greibach=True)  # TERM
        self._eliminer_regles_unitaires()  # UNIT
        self._segmenter_productions_complexes()  # DÉCOMPOSER_LONGUES_PRODUCTIONS

    # Méthodes privées pour les transformations en CNF et GNF
    def _introduire_axiome_depart(self) -> None:
        """
        Introduit un nouvel axiome en ajoutant un non-terminal supplémentaire.
        Ce nouveau non-terminal devient l'axiome de la grammaire et pointe
        vers l'ancien axiome dans ses règles de production.
        """

        # Générer un nouveau non-terminal qui n'existait pas encore.
        nouveau_axiome = generer_non_terminal(self.non_terminaux)
        self.non_terminaux.add(nouveau_axiome)

        # On crée une seule règle : nouveau_axiome -> (NON_TERMINAL, self.axiome).
        # Concrètement, si l'ancien axiome était "S0", on aura : S1 -> S0
        # et self.axiome passera à "S1".
        self.regles_de_production[nouveau_axiome] = [[('NON_TERMINAL', self.axiome)]]

        # Mettre à jour l'axiome de la grammaire pour qu'il soit ce nouveau symbole.
        self.axiome = nouveau_axiome

    def _remplacer_terminaux_dans_productions(self, greibach=False) -> None:
        """
        Remplace les terminaux dans des productions longues (c.-à-d., > 1 symbole)
        par des non-terminaux dédiés, garantissant ainsi :
         – Les terminaux n'apparaissent qu'en isolation dans certaines productions.
         – Approche spécifique si la transformation cible la GNF (Greibach).

        Si `greibach=True` :
         – Le premier symbole d'une production est laissé intact dans les transformations.

        :param greibach: bool, indique si la transformation cible la GNF (Greibach).
        """

        # Dictionnaire permettant de faire le lien entre un terminal (ex: 'a')
        # et un non-terminal généré (ex: 'T0'), afin de ne pas générer plusieurs fois
        # le même non-terminal pour un même terminal.
        assoc_terminaux = {}

        # Parcourir toutes les règles pour détecter les terminaux uniques
        # qui produisent directement un non-terminal existant.
        for non_terminal_gauche, productions_associees in self.regles_de_production.items():
            for production in productions_associees:
                # Si la production est de longueur 1, et que c'est un terminal,
                # alors on enregistre dans le dictionnaire pour pouvoir réutiliser
                # la même association terminal -> non-terminal.
                if len(production) == 1 and production[0][0] == "TERMINAL":
                    assoc_terminaux[production[0][1]] = non_terminal_gauche

        # Ce nouveau dictionnaire contiendra la version finale des règles
        # (sans modifier self.regles_de_production directement pendant la boucle).
        nouvelles_regles = {}

        # Dictionnaire temporaire pour stocker les règles (ex: T_a -> a)
        # des nouveaux non-terminaux créés au fil du parcours.
        regles_intermediaires = {}

        # Parcourir sans modifier self.regles_de_production pendant la boucle
        for non_terminal, productions_associees in self.regles_de_production.items():
            nouvelles_productions = []
            for production in productions_associees:
                # Si la production contient plus d'un symbole,
                # on remplace les terminaux par des non-terminaux.
                if len(production) > 1:
                    compteur_gb = 0

                    nouvelle_production = []
                    for (type_symbole, valeur_symbole) in production:
                        if greibach and compteur_gb == 0:
                            # Si c'est le premier symbole de la production,
                            # on conserve le symbole tel quel.
                            nouvelle_production.append((type_symbole, valeur_symbole))
                            compteur_gb += 1
                            continue

                        if type_symbole == "TERMINAL":
                            # Si ce terminal n'a pas encore été associé à un non-terminal
                            if valeur_symbole not in assoc_terminaux:
                                # Générer un nouveau non-terminal
                                nouveau_nt = generer_non_terminal(self.non_terminaux)
                                self.non_terminaux.add(nouveau_nt)

                                # Stocker la nouvelle règle dans regles_intermediaires
                                # Par exemple: T_a -> a
                                regles_intermediaires[nouveau_nt] = [[("TERMINAL", valeur_symbole)]]

                                # Mémoriser l'association 'a' -> T_a
                                assoc_terminaux[valeur_symbole] = nouveau_nt

                            # On remplace le terminal par le non-terminal correspondant
                            nouvelle_production.append(
                                ("NON_TERMINAL", assoc_terminaux[valeur_symbole])
                            )
                        else:
                            # Sinon, on recopie le symbole tel quel
                            nouvelle_production.append((type_symbole, valeur_symbole))

                    nouvelles_productions.append(nouvelle_production)
                else:
                    # Si la production est de longueur 1, pas besoin de changement
                    nouvelles_productions.append(production)

            # Après traitement, on stocke ces productions dans le dictionnaire final
            nouvelles_regles[non_terminal] = nouvelles_productions

        # Fusionner regles_intermediaires dans nouvelles_regles
        # (ajout des nouveaux non-terminaux créés en cours de route).
        for nouveau_nt, productions_creees in regles_intermediaires.items():
            nouvelles_regles[nouveau_nt] = productions_creees

        # Mettre à jour self.regles_de_production en une seule fois,
        # évitant ainsi l'erreur "dictionary changed size during iteration".
        self.regles_de_production = nouvelles_regles

    def _binariser_productions(self) -> None:
        """
        Réduit toutes les productions de la grammaire à des formes binaires,
        c'est-à-dire leur partie droite (à droite de l’:) ne contient au maximum que deux symboles.
        Utilise un cache pour éviter la duplication des non-terminaux intermédiaires.

        Exemple :
        S -> A B C devient S -> A X, où X -> B C.
        """

        # Dictionnaire où nous stockerons la version finale (binaire) des règles,
        # sans modifier self.regles_de_production directement pendant la boucle.
        nouvelles_regles = {}

        # Cache pour les suffixes déjà binarisés.
        # Clé : tuple représentant la partie droite d'une production (suffixe).
        # Valeur : ('NON_TERMINAL', nom_du_nt) déjà créé pour ce suffixe.
        cache_regles_binaires = {}

        # Parcourir les règles existantes
        for non_terminal, productions_associees in self.regles_de_production.items():
            nouvelles_productions = []
            for production in productions_associees:
                # Si la production a 2 symboles ou moins, elle respecte déjà
                # la contrainte binaire et n'a pas besoin d'être transformée.
                if len(production) <= 2:
                    nouvelles_productions.append(production)
                else:
                    # Sinon, on la binarise à l'aide d'une méthode récursive,
                    # tout en utilisant un cache pour éviter les duplications.
                    productions_binaires = self._en_binaire(
                        production, nouvelles_regles, cache_regles_binaires
                    )
                    # On ajoute les règles binaires obtenues
                    nouvelles_productions.extend(productions_binaires)

            # Après traitement, on assigne ces nouvelles productions
            # au non-terminal courant.
            nouvelles_regles[non_terminal] = nouvelles_productions

        # Une fois la boucle terminée, on remplace self.regles_de_production par la version binaire.
        self.regles_de_production = nouvelles_regles

        # Pour chaque non-terminal, on convertit la liste des productions en un set
        # (de tuples), puis on la retransforme en liste. Ainsi, s'il y a
        # S0 -> A1A2 en double, on n'en garde qu'un.
        for nt, productions in self.regles_de_production.items():
            # Convertir chaque production (liste) en tuple pour le set
            ensemble_productions = set(tuple(prod) for prod in productions)
            # Puis revenir à une liste de listes
            self.regles_de_production[nt] = [list(tup) for tup in ensemble_productions]

    def _en_binaire(self, production, nouvelles_regles, cache_regles_binaires) -> list:
        """
        Transforme récursivement une production en une suite de règles binaires.
        Utilise un cache (cache_regles_binaires) pour éviter de recréer plusieurs fois
        les mêmes non-terminaux pour un même suffixe.

        :param production: list, la production à binariser
        :param nouvelles_regles: dict, où stocker les éventuelles nouvelles règles
         pour les non-terminaux créés à la volée.
        :param cache_regles_binaires: dict, cache pour réutiliser les règles binaires déjà générées.
        :return: list, une liste de productions binaires (ex: [[A, X0]]).
        """

        # Si la production est déjà binaire ou unaire, on la renvoie telle quelle.
        if len(production) <= 2:
            return [production]

        def convertir_en_tuple_recursive(obj):
            """
            Convertit récursivement les listes en tuples, afin que l'objet
            puisse être utilisé comme clé dans le cache (car hachable).
            """
            if isinstance(obj, list):
                return tuple(convertir_en_tuple_recursive(e) for e in obj)
            return obj

        # On récupère la partie droite (suffixe) de la production,
        # puis on la convertit en tuple pour le cache.
        suffixe = production[1:]
        suffixe_tuple = convertir_en_tuple_recursive(suffixe)

        # Vérifier si on a déjà binarisé ce suffixe
        if suffixe_tuple in cache_regles_binaires:
            # Si oui, on réutilise le non-terminal qui lui était associé
            non_terminal_existant = cache_regles_binaires[suffixe_tuple]
            # On retourne directement la règle binaire [premier_symbole, non_terminal_existant]
            return [[production[0], non_terminal_existant]]

        # Sinon, on crée un nouveau non-terminal pour ce suffixe
        nouveau_non_terminal = generer_non_terminal(self.non_terminaux)
        self.non_terminaux.add(nouveau_non_terminal)

        # On enregistre dans le cache l'association suffixe -> ce nouveau non-terminal
        # sous forme ('NON_TERMINAL', nom).
        cache_regles_binaires[suffixe_tuple] = ("NON_TERMINAL", nouveau_non_terminal)

        # Construire la règle binaire initiale, par exemple si la production est
        # [A, B, C, D], on crée [A, (NON_TERMINAL, nouveau_non_terminal)].
        nouvelle_production = [production[0], ("NON_TERMINAL", nouveau_non_terminal)]

        # Initialiser la liste de règles pour ce nouveau non-terminal (s'il n'existe pas).
        if nouveau_non_terminal not in nouvelles_regles:
            nouvelles_regles[nouveau_non_terminal] = []

        # Poursuivre la binarisation sur le 'reste' : B, C, D
        sous_regles_binaires = self._en_binaire(suffixe, nouvelles_regles, cache_regles_binaires)

        # On ajoute ces sous-règles binaires aux règles du nouveau non-terminal.
        # Ainsi, nouveau_non_terminal -> sous_regles_binaires.
        nouvelles_regles[nouveau_non_terminal].extend(sous_regles_binaires)

        # On renvoie la règle binaire [A, (NON_TERMINAL, nouveau_non_terminal)]
        return [nouvelle_production]

    def _supprimer_productions_epsilon(self) -> None:
        """
        Supprime toutes les Epsilons-productions (produisant des chaînes vides)
        sauf si l'axiome lui-même est nullable (c.-à-d., qu'il peut générer une chaîne vide).
        Combine les productions existantes pour représenter les entités non-nullables.
        """

        # Identifier tous les non-terminaux nullables (pour éviter d'appeler _est_nullable() à chaque fois).
        ensemble_nullables = {nt for nt in self.non_terminaux if self._est_nullable(nt)}

        # Ce nouveau dictionnaire contiendra les règles après élimination d'Epsilon,
        # sans modifier self.regles_de_production directement pendant la boucle.
        nouvelles_regles = {}

        # Parcourir chaque non-terminal et ses productions
        for non_terminal_gauche, productions_associees in self.regles_de_production.items():
            nouvelles_productions = []

            # Pour chaque production, on génère toutes les combinaisons via la fonction
            # _generer_combinaisons, qui considère les symboles annulables (dans ensemble_nullables).
            for production in productions_associees:
                combinaisons = self._generer_combinaisons(production, ensemble_nullables)

                # On ne conserve la combinaison vide [] que si 'non_terminal_gauche' est l'axiome et qu'il fait
                # partie d'ensemble_nullables. Sinon, on ignore la combinaison vide.
                for c in combinaisons:
                    if c:
                        # Combinaison non vide => on la garde
                        nouvelles_productions.append(c)
                    else:
                        # c == [], la combinaison vide
                        # On l'autorise uniquement si c'est l'axiome et il est nullable
                        if non_terminal_gauche == self.axiome and non_terminal_gauche in ensemble_nullables:
                            # On remplace la production vide par [("EPSILON","E")]
                            nouvelles_productions.append([("EPSILON", "E")])

            # Filtrer dans une seule passe : on supprime les productions
            # [("EPSILON","E")] si le non-terminal n'est ni l'axiome ni nullable.
            liste_filtree = []
            for prod in nouvelles_productions:
                # Si c'est une production epsilon => on la garde seulement si c'est l'axiome nullable
                if len(prod) == 1 and prod[0][0] == "EPSILON":
                    if non_terminal_gauche == self.axiome and non_terminal_gauche in ensemble_nullables:
                        liste_filtree.append(prod)  # c'est autorisé pour l'axiome
                    else:
                        # Sinon, on supprime cette production epsilon
                        pass
                else:
                    # Production non vide => on la conserve
                    liste_filtree.append(prod)

            # Retirer les doublons éventuels : on convertit la liste en un set de tuples,
            # puis on revient en liste
            ensemble_productions_uniques = set(tuple(p) for p in liste_filtree)
            liste_filtree = [list(tup) for tup in ensemble_productions_uniques]

            # On stocke le résultat final pour 'non_terminal_gauche'
            nouvelles_regles[non_terminal_gauche] = liste_filtree

        # Mise à jour de self.regles_de_production en une seule fois
        self.regles_de_production = nouvelles_regles

        # Nettoyage final
        self.nettoyer_grammaire()

    @staticmethod
    def _generer_combinaisons(production, ensemble_nullables) -> list:
        """
        Génère toutes les combinaisons possibles pour une production,
        en tenant compte des symboles annulables.
        ex: si production = [(NON_TERMINAL, 'A1'), (NON_TERMINAL, 'B1')]
        et A1, B1 sont annulables, on peut avoir :
        [], [(NON_TERMINAL,'A1')], [(NON_TERMINAL,'B1')], [(NON_TERMINAL,'A1'),(NON_TERMINAL,'B1')]

        :param production: list, la production à traiter.
        :param ensemble_nullables: set, ensemble des non-terminaux annulables.
        :return: list, une liste de combinaisons possibles pour cette production.
        """
        combinaisons = [[]]

        for symbole in production:
            type_symbole, valeur_symbole = symbole

            # Si le symbole est un non-terminal annulable, on peut :
            # – soit le conserver
            # – soit l'omettre.
            if (type_symbole == "NON_TERMINAL") and (valeur_symbole in ensemble_nullables):
                # dupliquer toutes les combinaisons actuelles, en y ajoutant
                # ou pas ce symbole
                nouvelle_liste = []
                for c in combinaisons:
                    nouvelle_liste.append(c + [symbole])  # conserver
                for c in combinaisons:
                    nouvelle_liste.append(c)  # omettre
                combinaisons = nouvelle_liste
            else:
                # Sinon, on doit toujours le conserver
                combinaisons = [c + [symbole] for c in combinaisons]

        return combinaisons

    @lru_cache(maxsize=None)
    def _est_nullable(self, non_terminal: str, en_cours=frozenset()) -> bool:
        """
        Vérifie récursivement si un non-terminal est nullable.
        Un non-terminal est nullable si :
          - Il a une production explicite epsilon ('EPSILON').
          - Tous les symboles d'une règle sont nullables.

        Gère les cycles pour éviter les récursions infinies.
        :param non_terminal: Le non-terminal à vérifier.
        :param en_cours: Ensemble immuable (frozenset) des non-terminaux en cours d'évaluation.
        :return: True si le non_terminal est nullable, False sinon.
        """
        # Si on est déjà en train d'analyser 'non_terminal', on est dans un cycle.
        # On décide alors de ne pas le considérer comme nullable (pour éviter boucle infinie).
        if non_terminal in en_cours:
            return False

        # On ajoute le non-terminal courant à l'ensemble en cours
        nouveau_en_cours = en_cours | frozenset([non_terminal])

        # Parcourir toutes les productions de non_terminal
        for production in self.regles_de_production.get(non_terminal, []):
            # S'il existe une production [("EPSILON","E")], alors c'est nullable
            if len(production) == 1 and production[0][0] == 'EPSILON':
                return True

            # Sinon, si tous les symboles d'une production sont des non-terminaux annulables,
            # alors le non-terminal est nullable.
            # (ex: A -> B C, B et C étant annulables => A annulable)
            if all(
                    (sym[0] == 'NON_TERMINAL' and self._est_nullable(sym[1], nouveau_en_cours))
                    for sym in production
            ):
                return True

        # Si on n'a trouvé aucune production nullable, on renvoie False
        return False

    def _eliminer_regles_unitaires(self) -> None:
        """
        Supprime les règles unitaires, c'est-à-dire celles de la forme X -> Y,
        où X et Y sont des non-terminaux. Les règles X -> Y sont remplacées par
        les règles de production associées à Y.
        """

        # Construire un nouveau dictionnaire de règles
        nouvelles_regles = {nt: [] for nt in self.regles_de_production}

        # Éliminer les règles unitaires
        for non_terminal, productions in self.regles_de_production.items():
            a_visiter = set()  # non-terminaux trouvés via unité
            productions_finales = []  # productions non-unitaires

            # Séparer les règles unitaires (X->Y) des autres
            for production in productions:
                # production est une liste comme [(type, val)]
                if len(production) == 1 and production[0][0] == 'NON_TERMINAL':
                    # c'est une règle unitaire X->Y
                    a_visiter.add(production[0][1])
                else:
                    # on conserve les règles non-unitaires
                    productions_finales.append(production)

            # Explorer
            pile = list(a_visiter)
            while pile:
                courant = pile.pop()
                if courant in self.regles_de_production:
                    # On parcourt les productions de 'courant'
                    for p2 in self.regles_de_production[courant]:
                        # Si p2 est encore unitaire, on continue la chaîne
                        if len(p2) == 1 and p2[0][0] == 'NON_TERMINAL':
                            cible = p2[0][1]
                            if cible not in a_visiter:
                                a_visiter.add(cible)
                                pile.append(cible)
                        else:
                            # Sinon, c'est une production finale
                            if p2 not in productions_finales:
                                productions_finales.append(p2)

            # Mettre à jour les règles pour non_terminal
            nouvelles_regles[non_terminal] = productions_finales

        # Réaffecter à self.regles_de_production
        self.regles_de_production = nouvelles_regles

        # Nettoyages finaux
        self.nettoyer_grammaire()

    def _eliminer_recursivite_gauche(self) -> None:
        """
        Supprime toute récursivité gauche, qu'elle soit directe ou indirecte.
        La récursivité gauche directe est traitée d'abord, suivie de l'élimination
        de la récursivité gauche indirecte.
        Exemple pour une production directe :
        A -> A alpha | beta devient :
        A -> beta A'
        A' -> alpha A' | ε
        """

        while True:
            ancienne_regles = copy.deepcopy(self.regles_de_production)

            # Récupérer la liste de non-terminaux dans l'ordre (axiome en premier)
            ordered_nt = [self.axiome] + sorted(self.non_terminaux - {self.axiome})

            # Parcourir i de 0..(len(ordered_nt)-1)
            for i in range(len(ordered_nt)):
                ai = ordered_nt[i]
                # Si ai n'est plus présent (éventuellement supprimé ou vide), on saute
                if ai not in self.regles_de_production:
                    continue

                # Pour j=0..(i-1) => élimination de la récursivité gauche indirecte
                for j in range(i):
                    aj = ordered_nt[j]
                    if aj not in self.regles_de_production:
                        continue
                    # remplacer ai->aj gamma par ai->(prod_de_Aj) gamma
                    self._remplacer_productions(ai, aj)

                # Éliminer la récursivité gauche directe restante sur ai
                self._supprimer_recursivite_directe(ai)

            if ancienne_regles == self.regles_de_production:
                break

    def _remplacer_productions(self, Ai, Aj) -> None:
        """
        Remplace dans Ai toute production de la forme Ai->Aj gamma
        par Ai->(p) gamma pour chaque p dans les productions de Aj.
        Ex: Ai->Aj X  => Ai-> (delta1 X | delta2 X | ... ) si Aj->delta1|delta2|...

        :param Ai: Le non-terminal à traiter.
        :param Aj: Le non-terminal à remplacer.
        """
        if Ai not in self.regles_de_production or Aj not in self.regles_de_production:
            return

        anciennes = self.regles_de_production[Ai]
        nouvelles = []
        regles_aj = self.regles_de_production[Aj]

        for prod in anciennes:
            # prod est ex: [(NON_TERMINAL, 'Aj'), (TERMINAL, 'a'), ...]
            if len(prod) >= 1 and prod[0][0] == "NON_TERMINAL" and prod[0][1] == Aj:
                # => Ai->Aj + gamma
                gamma = prod[1:]  # la suite
                # Pour chaque production de Aj, on fabrique Aj_prod + gamma
                for pAj in regles_aj:
                    nouvelles.append(pAj + gamma)
            else:
                nouvelles.append(prod)

        self.regles_de_production[Ai] = nouvelles

    def _supprimer_recursivite_directe(self, Ai) -> None:
        """
        Supprime la récursivité gauche directe sur Ai :
          Ai->Ai alpha1 | ... | Ai alpha_n | beta1 | ... | beta_k
        devient
          Ai->beta1 Ai' | ... | beta_k Ai'
          Ai'->alpha1 Ai'| ... | alpha_n Ai' | EPSILON

        :param Ai: Le non-terminal à traiter.
        """
        if Ai not in self.regles_de_production:
            return

        productions = self.regles_de_production[Ai]
        alphas = []
        betas = []

        # Détecter les productions directes du type Ai->Ai ...
        for prod in productions:
            if len(prod) > 0 and prod[0][0] == "NON_TERMINAL" and prod[0][1] == Ai:
                # Ai->Ai alpha
                alphas.append(prod[1:])
            else:
                betas.append(prod)

        # S'il n'y a pas de récursivité gauche directe => on ne fait rien
        if not alphas:
            return

        # Sinon, on crée un nouveau non-terminal Ai'
        new_nt = generer_non_terminal(self.non_terminaux)
        self.non_terminaux.add(new_nt)

        # Ai -> beta new_nt  pour chaque beta
        nouvelles_prod_ai = []
        if not betas:
            # S’il n'y a pas de beta, on fait ex: Ai->Ai' (ou Ai->EPSILON??)
            # selon la convention (ex. algo standard => Ai-> Ai')
            # ou si on veut se rapprocher de la GN: Ai->Ai'
            nouvelles_prod_ai.append([("NON_TERMINAL", new_nt)])
        else:
            for beta in betas:
                nouvelles_prod_ai.append(beta + [("NON_TERMINAL", new_nt)])

        # Ai'-> alpha new_nt pour chaque alpha + EPSILON
        nouvelles_prod_aiprime = []
        for alpha in alphas:
            nouvelles_prod_aiprime.append(alpha + [("NON_TERMINAL", new_nt)])
        # Ajouter EPSILON
        nouvelles_prod_aiprime.append([("EPSILON", "E")])

        # On réassigne
        self.regles_de_production[Ai] = nouvelles_prod_ai
        self.regles_de_production[new_nt] = nouvelles_prod_aiprime

    def _segmenter_productions_complexes(self) -> None:
        """
        Décompose les longues productions contenant plus de deux symboles
        (non-terminaux ou terminaux) en une suite de productions intermédiaires.

        Exemple :
        S -> A B C devient :
        S -> A Z1, Z1 -> B C
        """

        # Nouveau dictionnaire pour stocker les règles modifiées
        nouvelles_regles = {}

        # On parcourt les règles actuelles pour chercher les longues productions
        for non_terminal, productions in self.regles_de_production.items():
            nouvelles_productions = []  # Règles pour ce non-terminal

            for production in productions:
                # Si la production a plus de 2 symboles
                if len(production) >= 2:
                    # Extraire le premier symbole de la production
                    premier_symbole = production[0]

                    # Rechercher ses règles dans le dictionnaire
                    if premier_symbole[0] == "NON_TERMINAL":
                        premier_symbole = premier_symbole[1]
                        regles_premier_symbole = self.regles_de_production.get(premier_symbole, [])

                        # On crée les combinaisons possibles
                        for regle_premier_symbole in regles_premier_symbole:
                            # On ajoute la combinaison à la production
                            nouvelle_production = regle_premier_symbole + production[1:]
                            nouvelles_productions.append(nouvelle_production)
                    else:
                        # Si le premier symbole est un terminal, on le conserve tel quel
                        nouvelles_productions.append(production)
                else:
                    # Si la production a 1 ou 0 symbole, on la conserve telle quelle
                    nouvelles_productions.append(production)

            # Mettre à jour les règles pour ce non-terminal
            nouvelles_regles[non_terminal] = nouvelles_productions

        # Fusionner avec les nouvelles règles créées
        self.regles_de_production.update(nouvelles_regles)

    # Nettoyage de la grammaire
    def nettoyer_grammaire(self) -> None:
        """
        Nettoie la grammaire en supprimant les non-terminaux inutiles.
        Les non-terminaux inutiles sont ceux qui ne peuvent pas générer de terminaux.
        """
        self.supprimer_non_terminaux_vides()
        self.supprimer_non_productifs()
        self.supprimer_non_terminaux_inaccessibles()

    def supprimer_non_terminaux_vides(self) -> None:
        """
        Supprime de la grammaire tous les non-terminaux sans aucune production associée.
        Ces non-terminaux ne contribuent en rien et peuvent être nettoyés.
        """
        a_supprimer = [nt for nt, productions in self.regles_de_production.items() if not productions]

        # Retirer ces non-terminaux vides
        for nt_vide in a_supprimer:
            del self.regles_de_production[nt_vide]
            if nt_vide in self.non_terminaux:
                self.non_terminaux.remove(nt_vide)

    def supprimer_non_terminaux_inaccessibles(self) -> None:
        """
        Identifie et supprime les non-terminaux inaccessibles à partir de l'axiome.
        Ces non-terminaux ne peuvent pas être atteints par un chemin à partir de l'axiome.
        """
        accessibles = set()
        pile = [self.axiome]

        while pile:
            courant = pile.pop()
            if courant not in accessibles:
                accessibles.add(courant)
                # On explore ses productions
                pile.extend(
                    val for prod in self.regles_de_production.get(courant, [])
                    for (typ, val) in prod if typ == "NON_TERMINAL"
                )

        # On ne conserve que ceux dans 'accessibles'
        regles_filtrees = {}
        for nt in self.regles_de_production:
            if nt in accessibles:
                regles_filtrees[nt] = self.regles_de_production[nt]

        # Diff pour voir lesquels ont été supprimés
        self.regles_de_production = regles_filtrees
        self.non_terminaux = set(regles_filtrees.keys())

    def supprimer_non_productifs(self) -> None:
        """
        Supprime de la grammaire tous les non-terminaux non-productifs,
        c'est-à-dire ceux qui ne mènent à aucun terminal ou chaîne utile.

        Exemple d'inutilité :
        A -> B (si B ne génère aucun terminal), alors A est également non-productif.
        """

        productifs = set()
        # On va itérer tant qu'on ajoute de nouveaux symboles
        modif = True
        while modif:
            modif = False

            for nt, liste_prods in self.regles_de_production.items():
                # Si nt est déjà productif, pas besoin de revérifier
                if nt in productifs:
                    continue

                # Vérifier si au moins une production de nt est 100% 'terminal'
                # ou 'non-terminal déjà dans productifs'
                for production in liste_prods:
                    # Si tous les symboles de la production sont :
                    #   - TERMINAL, ou
                    #   - NON_TERMINAL appartenant à productifs
                    # alors cette prod est "productrice".
                    est_productrice = True
                    for (typ, val) in production:
                        if typ == "NON_TERMINAL" and val not in productifs:
                            est_productrice = False
                            break
                        elif typ not in ("TERMINAL", "EPSILON", "NON_TERMINAL"):
                            # Cas inhabituel, selon votre logique...
                            est_productrice = False
                            break
                        elif typ == "NON_TERMINAL":
                            # On a déjà vérifié val in productifs
                            pass
                        # typ == "TERMINAL" ou "EPSILON" => c'est bon
                    if est_productrice:
                        productifs.add(nt)
                        modif = True
                        break  # plus besoin de checker les autres prods de nt

        # On enlève de la grammaire ceux qui ne sont pas dans productifs :
        non_productifs = set(self.regles_de_production.keys()) - productifs
        for np in non_productifs:
            del self.regles_de_production[np]
            if np in self.non_terminaux:
                self.non_terminaux.remove(np)

        # Enlever aussi, dans toutes les productions, les références
        # à des non-productifs qui traîneraient.
        for nt, liste_prods in self.regles_de_production.items():

            # On conserve les productions qui ne contiennent pas de non-productifs
            self.regles_de_production[nt] = [
                prod for prod in liste_prods
                if not any((typ == "NON_TERMINAL" and val in non_productifs) for (typ, val) in prod)
            ]

    def generer_mots(self, longueur: int) -> list:
        """
        Génère des mots à partir de la grammaire jusqu'à une certaine longueur.
        Les mots générés sont composés uniquement de terminaux, en tenant compte des EPSILON,
        et doivent respecter une production complète.

        :param longueur: Longueur maximale des mots générés.
        :return: Liste de mots générés par la grammaire.
        """
        if self.axiome is None:
            raise ValueError("La grammaire ne possède pas d'axiome défini.")

        mots_generes = set()

        def explorer(production_symboles, mot_actuel, profondeur):
            """
            Fonction récursive pour explorer les règles de la grammaire.

            :param production_symboles: Production actuelle (liste de symboles à traiter).
            :param mot_actuel: Mot en cours de construction.
            :param profondeur: Profondeur actuelle de la récursion pour limiter les appels excessifs.
            """
            # Si la profondeur ou la longueur du mot dépasse la limite, arrêter
            if profondeur > longueur or len(mot_actuel) > longueur:
                return

            # Si la production est vide et le mot est complet, ajouter aux résultats
            if not production_symboles:
                if all(sym[0] == "TERMINAL" for sym in mot_actuel):
                    mots_generes.add("".join(sym[1] for sym in mot_actuel))
                return

            # Traiter le premier symbole de la production
            symbole = production_symboles[0]
            reste = production_symboles[1:]

            if symbole[0] == "TERMINAL":
                # Ajouter le terminal au mot et continuer avec le reste
                explorer(reste, mot_actuel + [symbole], profondeur)
            elif symbole[0] == "NON_TERMINAL":
                # Explorer toutes les productions associées au non-terminal
                for prod in self.regles_de_production.get(symbole[1], []):
                    explorer(prod + reste, mot_actuel, profondeur + 1)
            elif symbole[0] == "EPSILON":
                # Si EPSILON, ignorer ce symbole et continuer avec le reste
                explorer(reste, mot_actuel, profondeur)

        # Lancer l'exploration à partir des productions de l'axiome
        for production in self.regles_de_production.get(self.axiome, []):
            explorer(production, [], 0)

        # Retourner les mots triés lexicographiquement
        return sorted(mots_generes)


# Gestion des fichiers
def lire(fichier: str) -> Grammaire:
    """
    Lit un fichier .general où chaque ligne décrit une ou plusieurs productions

    :param fichier: Chemin du fichier à lire.
    :return: Objet Grammaire contenant les règles de production.
    """
    # Initialisation d'un analyseur lexical pour interpréter les lignes du fichier
    analyseur = AnalyseurLexical()
    # Création d'une nouvelle instance de la classe Grammaire
    grammaire = Grammaire()

    # Ouverture et lecture du fichier ligne par ligne
    with open(fichier, "r", encoding="utf-8") as f:
        for num_ligne, ligne in enumerate(f, start=1):
            # Suppression des espaces inutiles au début et à la fin de la ligne
            ligne = ligne.strip()
            if not ligne:
                # Ignorer les lignes vides
                continue

            # Analyse lexicale pour découper la ligne en tokens
            tokens = analyseur.analyser_texte(ligne)
            if len(tokens) < 2:
                # Afficher une erreur si la syntaxe est incorrecte
                print(f"Erreur de syntaxe ligne {num_ligne}: {ligne}")
                continue

            # Le premier token est le non-terminal à gauche de la règle
            non_terminal_gauche = tokens[0].value
            if grammaire.axiome is None:
                # Si aucun axiome n'est défini, définir le premier non-terminal comme axiome
                grammaire.set_axiome(non_terminal_gauche)

            productions_associees = []  # Liste pour stocker les productions associées
            production_acutelle = []  # Temporaire pour construire une production

            # Analyse des tokens suivants pour construire les productions
            for token in tokens[2:]:
                if token.type == "PIPE":
                    # Si un séparateur '|' est rencontré, sauvegarder la production actuelle
                    if production_acutelle:
                        productions_associees.append(production_acutelle)
                    production_acutelle = []
                else:
                    # Ajout des tokens à la production courante
                    if token.type == "NON_TERMINAL":
                        production_acutelle.append(("NON_TERMINAL", token.value))
                    elif token.type == "TERMINAL":
                        production_acutelle.append(("TERMINAL", token.value))
                    elif token.type == "EPSILON":
                        production_acutelle.append(("EPSILON", 'E'))

            # Ajouter la dernière production si elle n'est pas vide
            if production_acutelle:
                productions_associees.append(production_acutelle)

            # Ajouter les productions associées au non-terminal
            grammaire.ajouter_regle(non_terminal_gauche, productions_associees)

    # Nettoyage final de la grammaire (suppression des règles inutiles)
    grammaire.nettoyer_grammaire()

    # Retourner l'objet Grammaire complet
    return grammaire


def ecrire(grammar: Grammaire, fichier_base: str, extension: str) -> None:
    """
    Exporte la grammaire transformée dans un fichier avec l'extension choisie.
    :param grammar: Objet Grammaire à exporter.
    :param fichier_base: Chemin du fichier d'origine.
    :param extension: Extension à ajouter au fichier de sortie.
    """
    # On remplace l'extension du fichier_base par .<extension>
    fichier_sortie = fichier_base.rsplit('.', 1)[0] + '.' + extension

    with open(fichier_sortie, "w", encoding="utf-8") as f_out:
        axiome = grammar.axiome
        # Écriture de l'axiome en premier, si présent
        if axiome in grammar.regles_de_production:
            productions_axiome = grammar.regles_de_production[axiome]
            if productions_axiome:
                parties_axiome = []
                for prod in productions_axiome:
                    # On fabrique la partie droite (ex: "X1 X2" ou "E" etc.)
                    partie_droite = "".join(sym[1] for sym in prod)
                    parties_axiome.append(partie_droite)
                f_out.write(f"{axiome} : {' | '.join(parties_axiome)}\n")

        # Puis écrire les autres NT (hors axiome)
        tous_nt = sorted(grammar.regles_de_production.keys())
        for non_terminal in tous_nt:
            if non_terminal == axiome:
                continue
            prods = grammar.regles_de_production[non_terminal]

            parties = []
            for prod in prods:
                partie_droite = "".join(sym[1] for sym in prod)
                parties.append(partie_droite)
            f_out.write(f"{non_terminal} : {' | '.join(parties)}\n")

