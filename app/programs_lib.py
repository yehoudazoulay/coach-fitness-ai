"""Bibliothèque de programmes "type" (templates) + consignes de la phase programme.

Approche hybride : la STRUCTURE saine est dans les templates (validés), le LLM ne
fait que SÉLECTIONNER + ADAPTER (dispos, blessures, matériel) et présenter dans la
voix du coach. On démarre avec 1 template pour tester le flux ; à enrichir ensuite.

⚠️ Templates de départ basés sur des principes classiques — à faire relire par un
coach diplômé avant une vraie mise en prod.
"""

import json

# --- Templates ---------------------------------------------------------------

TEMPLATES: dict[str, dict] = {
    "fullbody_debutant_3x": {
        "id": "fullbody_debutant_3x",
        "name": "Full-body débutant — 3 séances/semaine",
        "objectif": "remise en forme / recomposition / perte de gras",
        "niveau": "débutant",
        "frequence": 3,
        "principes": "3 séances full-body identiques dans la structure, un jour de "
        "repos entre chaque, progression en ajoutant du poids ou des reps chaque "
        "semaine. Simple et tenable.",
        "seances": [
            {
                "nom": "Séance full-body (A/B/C, même schéma)",
                "exos": [
                    {"exo": "Squat (ou goblet squat)", "series": 3, "reps": "8-12"},
                    {"exo": "Développé couché haltères (ou pompes)", "series": 3, "reps": "8-12"},
                    {"exo": "Rowing haltère (ou tirage)", "series": 3, "reps": "8-12"},
                    {"exo": "Fentes (ou presse)", "series": 3, "reps": "10-12"},
                    {"exo": "Gainage (planche)", "series": 3, "reps": "30-45 s"},
                ],
            }
        ],
    },
}

DEFAULT_TEMPLATE = "fullbody_debutant_3x"


def template_json(template_id: str | None = None) -> str:
    t = TEMPLATES.get(template_id or DEFAULT_TEMPLATE, TEMPLATES[DEFAULT_TEMPLATE])
    return json.dumps(t, ensure_ascii=False, indent=2)


# --- Consignes de la phase PROGRAMME (injectées dans le system prompt) -------

PROGRAM_INSTRUCTIONS = """\
PHASE PROGRAMME : la découverte est finie, place au programme.

D'ABORD, demande-lui s'il a DÉJÀ un programme qu'il suit / veut suivre, ou s'il \
veut que tu lui en construises un.
- S'IL A DÉJÀ UN PROGRAMME : pars du SIEN. Demande-lui de te le décrire, jette un \
œil de coach (signale franchement, dans ta voix, si un truc cloche, manque ou est \
risqué — sans tout réécrire de force), ajuste avec lui si besoin, puis valide-le.
- SINON : propose-lui-en un en t'appuyant sur le TEMPLATE ci-dessous (structure \
saine, validée) que tu ADAPTES : cale les séances sur ses jours/dispos, remplace \
les exos selon ses blessures (events) ou son matériel, reste réaliste vs sa \
fréquence, sa durée et son niveau.

Si ses horaires sont FLEXIBLES (pas de jours fixes, ça dépend du boulot) : ne fige \
PAS des jours précis. Construis un programme de N séances/semaine à caser quand il \
peut, et dis-lui clairement l'objectif = tenir ce nombre de séances chaque semaine.

Dans les deux cas : présente/discute CLAIREMENT (séances, exos, séries/reps) dans \
TA voix — cash, direct, un peu marrant — et ajuste AVEC lui. Un programme simple \
et tenable vaut mieux qu'un truc parfait. Quand il est d'accord, tu le VALIDES \
explicitement (genre : "OK, c'est parti là-dessus."). Tu n'inventes pas de science \
exotique.

PRINCIPES À RESPECTER (non négociables, c'est la base saine — tu ne proposes JAMAIS \
un truc qui les viole) :
- RÉCUPÉRATION : en full-body, il faut au moins un jour de repos entre deux séances \
— jamais deux full-body d'affilée. Même en planning FLEXIBLE, dis-lui clairement \
d'espacer ses séances (pas 2 jours de suite), le muscle grandit au repos.
- PROGRESSION : rappelle-lui d'augmenter progressivement (charge ou répétitions) \
au fil des semaines, sinon ça stagne.
- Reste réaliste : mieux vaut un peu et bien récupéré que beaucoup et cramé.

TEMPLATE DE DÉPART (si tu dois en proposer un) :
{template}
"""


def program_instructions(template_id: str | None = None) -> str:
    # 1 seul template pour l'instant ; la sélection multi-templates viendra avec
    # l'enrichissement de la bibliothèque.
    return PROGRAM_INSTRUCTIONS.format(template=template_json(template_id))
