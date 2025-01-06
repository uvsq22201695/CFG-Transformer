# Définitions
PYTHON=python
GENERAL_FILES=$(wildcard *.general)
GENERER=generer.py
GRAMMAIRE=grammaire.py
N?=4  # Par défaut, N vaut 4, mais peut être redéfini lors de l'appel à make

# Par défaut, on génère les fichiers .chomsky et .greibach pour chaque fichier .general
all: $(GENERAL_FILES:.general=.chomsky) $(GENERAL_FILES:.general=.greibach)

%.chomsky: %.general
	$(PYTHON) $(GRAMMAIRE) $<

%.greibach: %.general
	$(PYTHON) $(GRAMMAIRE) $<

# Tester la génération des mots à partir des fichiers .chomsky et .greibach
test:
	for file in $(GENERAL_FILES:.general=.chomsky); do \
		base=$$(basename $$file .chomsky); \
		res_file=$${base}_${N}_chomsky.res; \
		$(PYTHON) $(GENERER) $(N) $$file > $$res_file; \
	done

	for file in $(GENERAL_FILES:.general=.greibach); do \
		base=$$(basename $$file .greibach); \
		res_file=$${base}_${N}_greibach.res; \
		$(PYTHON) $(GENERER) $(N) $$file > $$res_file; \
	done

	for base in $(basename $(GENERAL_FILES)); do \
		diff -u $${base}_${N}_chomsky.res $${base}_${N}_greibach.res || echo "Différences détectées pour $$base"; \
	done

# Nettoyage des fichiers générés
clean:
	rm -f *.chomsky *.greibach
	rm -f *_chomsky.res *_greibach.res

# Informations d'aide
help:
	@echo "Commandes disponibles :"
	@echo "  make                   - Génère les fichiers .chomsky et .greibach"
	@echo "  make N=<longueur> test - Spécifie la longueur des mots à générer (ex : make N=5 test)"
	@echo "  make clean             - Supprime les fichiers générés"
	@echo "  make help              - Affiche ce message d'aide"o
