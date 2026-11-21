# Assistant de conformité RGPD basé sur les sanctions de la CNIL

> Projet en cours

Un assistant qui aide les PME à évaluer si un projet impliquant des données personnelles respecte le RGPD, en s'appuyant sur les vraies sanctions prononcées par la CNIL. Il combine un **RAG** et un **graphe de connaissances** (Neo4j) pour retrouver des cas similaires et les relier entre eux.

## Le problème

Une PME qui lance un nouveau traitement de données (vidéosurveillance, newsletter, fichier clients, outil RH…) doit s'assurer qu'elle respecte le RGPD. Mais elle n'a souvent ni juriste ni DPO, et personne ne lit des centaines de décisions de la CNIL pour savoir ce qui est risqué.

## La solution

L'utilisateur décrit sa situation en langage naturel :

> « Nous voulons installer des caméras dans notre entrepôt pour éviter les vols, filmer en continu les zones où travaillent nos salariés et garder les images 3 mois. Est-ce conforme au RGPD ? »

L'assistant répond avec :

- **les risques** identifiés pour cette situation (ici : surveillance permanente des salariés, durée de conservation trop longue) ;
- **des sanctions similaires** prononcées par la CNIL depuis 2018, avec le montant, la date et le lien vers la décision ;
- **les articles du RGPD** concernés et ce qu'ils exigent ;
- **les actions à mettre en place** pour être en règle.

## Pourquoi un graphe ?

Un RAG classique retrouve les textes **qui se ressemblent** à la question. Il ne peut donc pas répondre à : *« Quelles entreprises ont été sanctionnées pour le même manquement que Free ? »*. Les décisions concernant les autres entreprises ne parlent pas de Free.

Le graphe, lui, relie les décisions **qui sont liées**. Free est reliée à sa sanction, cette sanction est reliée au manquement en cause, et ce manquement est relié à toutes les autres entreprises sanctionnées pour la même raison. Il suffit de suivre les liens.

```
(Organisme)-[:SANCTIONNE_PAR]->(Decision)-[:VIOLE]->(Article RGPD)
(Decision)-[:CONCERNE]->(Manquement)
(Organisme)-[:APPARTIENT_A]->(Secteur)
```

Le projet compare les deux approches (RAG classique vs GraphRAG) sur un même jeu de questions, chiffres à l'appui.

## Questions types

**Simples** (la réponse est dans une seule décision)
1. Pourquoi Free a-t-elle été sanctionnée par la CNIL ?
2. Que reproche la CNIL à une entreprise qui conserve des images de vidéosurveillance trop longtemps ?
3. Que dit l'article 32 du RGPD sur la sécurité des données ?

**Multi-documents** (il faut croiser plusieurs décisions)

4. Quelles entreprises ont été sanctionnées pour le même manquement que Free ?
5. Quelles sanctions concernent la surveillance des salariés ?
6. Quels manquements reviennent le plus souvent chez les entreprises du e-commerce ?
7. Je veux envoyer une newsletter à mes clients : quels risques, et y a-t-il eu des sanctions sur des cas proches ?

**Statistiques** (il faut compter ou calculer)

8. Quel est le montant moyen des sanctions liées aux cookies ?
9. Quel article du RGPD est le plus souvent cité dans les sanctions ?
10. Combien de sanctions la CNIL a-t-elle prononcées chaque année depuis 2018 ?

## Données

[Délibérations de la CNIL](https://huggingface.co/datasets/AgentPublic/cnil) (open data DILA, licence Etalab 2.0), filtrées sur les sanctions et mises en demeure depuis l'entrée en application du RGPD (mai 2018).

## Stack

| Rôle | Outil |
|---|---|
| Langage | Python, uv |
| Base graphe | Neo4j Aura |
| LLM et embeddings | Mistral |
| Orchestration | LangChain |
| Évaluation | RAGAS |
| API | FastAPI |
| Interface | Streamlit |
| Déploiement | Docker |

## Structure du projet

```
cnil-graphrag/
├── api/                  API FastAPI
├── app/                  interface Streamlit
├── data/                 données (non versionnées)
├── notebooks/            exploration
└── src/cnil_graphrag/
    ├── ingestion/        récupération et filtrage des données
    ├── extraction/       extraction des entités avec le LLM
    ├── graph/            construction du graphe Neo4j
    ├── rag/              RAG classique et GraphRAG
    └── eval/             comparaison des deux approches
```

## Installation

```bash
git clone https://github.com/alixhomet/cnil-graphrag.git
cd cnil-graphrag
uv sync
```

## Résultats

_À venir : comparaison RAG classique vs GraphRAG._
