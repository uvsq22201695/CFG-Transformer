from ply import lex

class AnalyseurLexical:
    # Liste des tokens
    tokens = ('REGLE', 'NON_TERMINAL', 'TERMINAL', 'PIPE', 'EPSILON')

    # Règles pour les éléments de la grammaire
    t_REGLE = r':'
    t_PIPE = r'\|'
    t_TERMINAL = r'[a-z]'
    t_EPSILON = r'E'

    # Ignorer les espaces et les tabulations
    t_ignore = ' \t'

    def __init__(self):
        """
        Initialise l'analyseur lexical.
        """
        self.lexer = lex.lex(module=self)

    # Règle modifiée pour les non-terminaux (avec espace facultatif)
    def t_NON_TERMINAL(self, t):
        r'[A-DF-Z]\s*[0-9]'

        # Supprimer les espaces dans la valeur du token
        t.value = t.value.replace(' ', '')

        return t

    def analyser_texte(self, texte: str) -> list:
        """
        Analyse une ligne de texte représentant une règle.
        :param texte: Du texte.
        :return: Liste des tokens trouvés.
        :raises ValueError: Si un caractère non reconnu est détecté.
        """
        self.lexer.input(texte)
        tokens = []
        while True:
            token = self.lexer.token()
            if not token:
                break
            tokens.append(token)

        return tokens

    def t_error(self, t):
        """
        Gère les erreurs lexicales.
        """
        raise ValueError(f"Caractère inattendu : «{t.value[0]}» à la position {t.lexpos} dans «{t.lexer.lexdata}»")

