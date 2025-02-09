# CFG-Transformer

CFG-Transformer est un outil permettant la transformation des grammaires hors contexte (CFG - Context-Free Grammar) en Forme Normale de Chomsky (CNF) et Forme Normale de Greibach (GNF). Ce projet vise à faciliter l'analyse syntaxique et la modélisation des langages formels, notamment en compilation et en traitement automatique du langage.

## Description

L'objectif de ce projet est d'automatiser la conversion des grammaires contextuelles en différentes formes normales, tout en garantissant la préservation de leur langage initial. Il permet de simplifier l'étude des grammaires en facilitant leur utilisation dans des algorithmes d'analyse syntaxique.

## Fonctionnalités

- Transformation de grammaires contextuelles en CNF et GNF.
- Gestion des règles récursives et des productions multiples.
- Vérification et simplification automatique des grammaires.
- Interface en ligne de commande pour tester les transformations.

## Installation

### Prérequis

- Python 3.11
- ply~=3.11

### Clonage du dépôt

```bash
git clone https://github.com/uvsq22201695/CFG-Transformer.git
cd CFG-Transformer
```

### Exécution

L'exécution se fait via le fichier `Makefile`. Tout les fichiers ayant l'extension .general seront convertis.

```bash
make
```

Pour tester la génération des mots :

```bash
make N=<longueur> test
```

Pour nettoyer les fichiers générés :

```bash
make clean
```

Pour avoir de l'aide sur les commandes :
```bash
make help
```

## Format des grammaires acceptées

Les fichiers de grammaires sont sous la forme suivante :

```
S0 : A1S0B1 | C1
A1 : a
B1 : b
C1 : c | E
```
