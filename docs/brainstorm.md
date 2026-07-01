# Coach Fitness WhatsApp — Brainstorming

> Document vivant. Capture les idées + leur ancrage scientifique. Rien n'est figé.
> Dernière maj : 2026-06-30

---

## 1. Vision en une phrase

Un coach IA accessible **uniquement via WhatsApp** qui, après une **discussion de découverte**, attribue/adapte un **profil de coach** à la personnalité de l'utilisateur, puis le suit **proactivement** dans la durée — le tout **calibré par de la vraie psychologie du changement de comportement**, pas juste un ton "marrant" ou "militaire" plaqué.

Principe directeur : **le style est la surface, la science est le moteur.** Le ton (humour, militaire…) change l'emballage ; les leviers qui font vraiment changer les comportements (autonomie, compétence, habitudes) restent actifs sous le capot quel que soit le style choisi.

---

## 2. La discussion de découverte (le cœur du calibrage)

Objectif : poser **le curseur au bon endroit** (niveau d'implication du coach, ton, fréquence des relances) ET récolter les données fitness de base. Menée en conversation naturelle sur WhatsApp, pas un formulaire froid.

> 🎙️ **C'est le HEAD COACH qui mène l'entretien**, pas une voix neutre. Le Head Coach est un personnage à part entière (le boss/fondateur du programme) : il accueille, fait passer la découverte de façon humaine et drôle, puis **matche et attribue le coach dédié** au moment du handoff. Détails dans [coachs.md](coachs.md).

### 2.1 Deux blocs de questions

**A. Bloc "fitness / lifestyle" (les faits)**
- Objectif principal (perte de gras, prise de muscle, santé, performance, bien-être…)
- Niveau actuel & historique sportif
- Alimentation (habitudes, contraintes, régime particulier)
- Hygiène de vie : sommeil, stress, alcool, tabac, sédentarité (travail)
- Contraintes : temps dispo/semaine, matériel, blessures, santé
- Échéance / pourquoi maintenant (l'événement déclencheur)

**B. Bloc "psychologique" (le calibrage du coaching)**
- Réaction au challenge / à l'échec → *cf. Regulatory Focus (§5.5)*
- Source de motivation : pour soi vs regard des autres → *cf. SDT (§5.1)*
- Préférence de ton : encouragement doux vs cadrage ferme vs humour vs data brute
- Tolérance à la pression et à la culpabilisation (certains détestent, d'autres en redemandent)
- Niveau d'autonomie souhaité : "dis-moi exactement quoi faire" vs "guide-moi, je décide"
- Fréquence de contact désirée (du daily au hebdo)
- Stade de changement actuel → *cf. Transthéorique (§5.2)* : est-il déjà en action ou juste en train d'y penser ?

### 2.2 Ce que la découverte produit (sortie structurée)

Un **profil utilisateur** exploitable par le moteur :
```
- objectif, contraintes, niveau
- style_coach proposé (+ pourquoi)
- traits ajustables (curseurs, cf. §3.2) initialisés
- niveau_implication (fréquence + intensité des relances)
- focus motivationnel (promotion / prévention)
- stade de changement
- déclencheurs personnels (le "why")
```

> ⚠️ **Honnêteté scientifique importante.** La science (SDT, Motivational Interviewing) montre que les approches **culpabilisantes / contrôlantes** sont efficaces à *court* terme mais **sabotent la motivation à long terme** et augmentent l'abandon. Donc :
> - On propose un style "militaire/culpabilisant" parce que **certains le demandent et adorent** → ça reste un choix produit légitime.
> - MAIS on le conçoit comme un **ton de surface**, en gardant dessous des mécaniques qui soutiennent l'autonomie. Et la découverte sert justement à **détecter qui supporte vraiment ce registre** vs qui décrochera.

---

## 3. Les profils de coach

> ⭐ **Les coachs sont un CASTING FIXE de personnages déjà écrits — pas générés à la volée.** Chaque coach existe "en stock" avec un **prénom + nom**, une **vie/backstory**, et une **personnalité forte et cohérente**. On ne crée pas un coach pour l'utilisateur : la découverte **matche l'utilisateur avec le coach du casting qui lui correspond le mieux**. Seuls les **curseurs** (§3.2) s'ajustent par-dessus. C'est ça qui crée l'attachement et la rétention — on s'attache à *quelqu'un de réel et mémorable*, pas à un "style n°3".
>
> Avantages : personnages riches et soignés (écrits à la main, testés), cohérence garantie, et l'utilisateur a l'impression de "rencontrer" quelqu'un. La bible des coachs vit dans **[coachs.md](coachs.md)**.

### 3.1 Le casting (roster de coachs pré-définis)

Chaque coach = un personnage complet et figé dans son identité. Exemples d'archétypes à incarner (les vrais personnages, leurs noms et vies sont dans [coachs.md](coachs.md)) :
- **Le/la bienveillant·e** — chaleureux, encourageant, sans jugement
- **Le/la militaire** — direct, cadrant, "pas d'excuses", discipline
- **Le/la marrant·e / pote** — humour, légèreté, complicité
- **Le/la data / analytique** — factuel, chiffres, optimisation, peu d'émotion
- **Le/la culpabilisant·e** — rappelle l'objectif, joue sur l'engagement (⚠️ voir avertissement §2.2)
- *(à enrichir)*

Techniquement, chaque coach = une **fiche personnage** (prénom, nom, genre, backstory, traits, façon de parler, réactions types) qui se compile en un bloc de system prompt. La fiche est **fixe** ; seuls les curseurs varient selon l'utilisateur.

### 3.2 Traits ajustables (par-dessus le profil)

Quel que soit le profil choisi, l'utilisateur (et la découverte) règlent des **curseurs** :
- **Humour** (sobre ←→ blagueur)
- **Niveau d'implication** (léger ←→ intense : fréquence + insistance des relances)
- **Fermeté** (doux ←→ cadrant)
- **Verbosité** (concis ←→ détaillé)
- **Familiarité** (vouvoiement/pro ←→ tutoiement/pote)
- **Exigence sur le suivi** (optionnel ←→ "je veux ta photo repas tous les jours")

→ Architecture : `system_prompt = profil_de_base + curseurs + profil_utilisateur + état_courant`. Les curseurs sont des variables injectées, modifiables à tout moment ("coach, sois moins relou sur les rappels" → on baisse le curseur implication).

### 3.3 Le coach parle "humain" (adaptation linguistique dynamique)

Au-delà du profil et des curseurs (qui sont des réglages explicites), le coach doit **s'aligner sur la façon de parler de l'utilisateur** pour sonner humain, pas robotique. Distinct du style : deux personnes avec le même profil "bienveillant" ne se font pas parler pareil.

Ce qui s'adapte, en miroir de l'utilisateur :
- **Registre & vocabulaire** : soutenu vs familier vs argot/vannes
- **Longueur des messages** : si l'utilisateur écrit court, le coach écrit court
- **Rythme & ponctuation** : emojis ou pas, messages hachés vs phrases construites
- **Langue / code-switching** : français, anglais, mélange, expressions locales
- **Niveau d'énergie** : posé vs hype

Comment :
- Quelques **règles dans le system prompt** ("adapte ton registre, ta longueur et ton usage des emojis à ceux de l'utilisateur ; reste naturel, jamais robotique").
- Renforcé par le **profil** (familiarité/verbosité, cf. §3.2) et le **résumé glissant** (§9.2) qui note le style de com observé.
- Garder une **cohérence de personnalité** : le coach s'adapte au coachee SANS perdre l'identité de son profil (un militaire reste militaire, mais cale son langage sur la personne).

**Science :** Communication Accommodation Theory (Giles) + Linguistic Style Matching — l'alignement du style de langage augmente le rapport, la confiance et le sentiment de connexion. C'est un levier direct de la composante "lien/appartenance" de la SDT (§5.1).

> ⚠️ Limite : adaptation ≠ imitation servile. Pas de "yes-man". Le coach reste capable de cadrer/contredire (cf. avertissement §2.2) — il ajuste son *langage*, pas ses *principes*.

---

## 4. La proactivité du coach (le moteur de rétention)

Le coach **initie** le contact, calibré par le niveau d'implication + la découverte :
- **Rappels** : "t'as ta séance aujourd'hui 💪", relance si inactif
- **Félicitations / encouragements** : après une séance, un objectif atteint, une série de jours
- **Demandes d'infos** : photo repas, photo physique (suivi), poids, sommeil, niveau d'énergie/stress
- **Check-ins programmés** : hebdo sur le poids, mensuel sur les photos…

Tout est **paramétrable** et **borné par la découverte** (un utilisateur "faible implication" reçoit peu ; un "intense" reçoit du quotidien).

> ⚙️ **Note technique WhatsApp** : les messages proactifs (hors fenêtre 24h après le dernier message user) nécessiteront des **templates approuvés par Meta** en prod. En sandbox c'est permissif. À garder en tête pour l'archi des relances. Le scheduler (APScheduler) est déjà en place, désactivé par défaut.

> 🔒 **Données sensibles** : photos physiques, poids, sommeil = données personnelles (et de santé). À traiter avec consentement explicite, stockage carré, et conformité (RGPD) dès qu'on a de vrais users.

---

## 5. Fondations scientifiques (le "backup" demandé)

Chaque idée ci-dessus s'appuie sur un cadre établi. À utiliser pour concevoir le questionnaire ET les comportements du coach.

### 5.1 Self-Determination Theory (Deci & Ryan)
La motivation durable repose sur 3 besoins : **autonomie** (je choisis), **compétence** (je progresse), **appartenance/lien** (relation au coach). → Le coach doit nourrir les 3. C'est l'argument central contre le coaching purement contrôlant.

### 5.2 Modèle Transthéorique / Stades du changement (Prochaska & DiClemente)
Pré-contemplation → contemplation → préparation → action → maintien. → La découverte situe l'utilisateur ; le coach n'attaque pas un "contemplatif" comme un "en action".

### 5.3 BCT Taxonomy (Michie et al.)
Catalogue validé de ~93 "techniques de changement de comportement" (auto-monitoring, feedback, goal-setting, rappels, récompense…). → Bibliothèque concrète de ce que le coach peut *faire*. Le suivi du poids/photos = "self-monitoring", une des BCT les plus efficaces.

### 5.4 Motivational Interviewing (Miller & Rollnick)
Style d'entretien qui fait émerger la motivation *de la personne* plutôt que de l'imposer. → Inspire le ton de la découverte (questions ouvertes, écoute, pas de leçon).

### 5.5 Regulatory Focus Theory (Higgins)
Deux moteurs : **promotion** (recherche de gains, "deviens plus fort") vs **prévention** (évitement de pertes, "ne pas régresser/se blesser"). → Détecté en découverte ("réaction au challenge"), il oriente la formulation des messages.

### 5.6 Goal-Setting Theory (Locke & Latham) + objectifs SMART
Objectifs spécifiques, mesurables, ambitieux mais atteignables → meilleure performance. → Structure la définition d'objectif en découverte.

### 5.7 Habitudes & intentions d'implémentation (Gollwitzer ; Clear, *Atomic Habits*)
Les plans "si X alors Y" ("après le café du matin, je fais 10 min de mobilité") et les boucles d'habitude battent la motivation pure. → Le coach aide à *installer des habitudes*, pas juste à motiver.

### 5.8 Big Five (OCEAN) — calibrage du ton
Le profil de personnalité (ex. extraversion, névrosisme) prédit quel registre passe le mieux. → Sous-tend l'attribution du profil de coach. (Inutile d'administrer un test complet : quelques items suffisent.)

---

## 6. Points de vigilance

- **Éthique du style "culpabilisant"** : à proposer mais avec garde-fou (cf. §2.2). Possibilité d'un message d'avertissement / opt-in conscient.
- **Pas de conseil médical** : la partie compléments/sang viendra plus tard, isolée, avec disclaimers. Le coach lifestyle ne doit pas déraper en prescription santé.
- **Données de santé** : consentement, sécurité, RGPD dès les vrais users.
- **Sur-sollicitation** : trop de relances = blocage/désabonnement. Le niveau d'implication doit pouvoir baisser facilement à la demande.
- **Validation** : idéalement faire relire la logique psy par un pro (coach diplômé / psy) avant d'en faire un argument marketing.

---

## 7. Questions ouvertes (à trancher)

1. **Attribution du style** : 100% automatique (l'IA décide d'après la découverte) ou proposé puis **validé/choisi** par l'utilisateur ? (recommandé : proposé + ajustable → renforce l'autonomie, cf. SDT)
2. **Longueur de la découverte** : courte (5-6 questions, friction minimale) ou approfondie (meilleur calibrage mais risque d'abandon) ? Compromis possible : noyau court + enrichissement progressif au fil des échanges.
3. **Combien de profils** au lancement ? (commencer avec 3-4 bien faits > 8 bâclés)
4. **Changement de style** en cours de route : autorisé librement, ou le coach le suggère s'il détecte que ça ne prend pas ?
5. **Where to store** le profil/curseurs : déjà en SQLite (table `users` a `style`, `state`) — à étendre avec les traits + profil structuré.

---

## 8. Prochaine étape technique proposée

Phase 3 = transformer la discussion libre actuelle en **vrai parcours de découverte** :
1. Définir le **set de questions** (noyau court, ancré §2 + §5)
2. Étendre le schéma `users` (traits, focus motivationnel, stade, objectif…)
3. Logique : à la fin de la découverte → l'IA **propose un profil + curseurs** → l'utilisateur valide/ajuste → passage en `state=active`
4. Injecter profil + curseurs dans le system prompt (déjà l'archi de `coach.py`)

---

## 9. Mémoire & stockage des conversations

Question tranchée : **les deux (structuré + brut), en couches — et le vectoriel PLUS TARD, pas au MVP.**

Principe : un coach n'a pas besoin de relire des milliers de messages, il a besoin de **quelques faits à jour**. Le structuré est donc la mémoire *principale* ; le vectoriel n'est qu'une couche de rappel sémantique optionnelle.

### 9.1 Les 3 couches

```
Couche 1 — FAITS STRUCTURÉS    → DB relationnelle (SQLite → Postgres)
   "ce que le coach SAIT"          ← LU à chaque message
   poids, objectif, contraintes, préférences, style/curseurs,
   adhérence (séances faites/ratées), blessures, sommeil...

Couche 2 — TRANSCRIPT BRUT     → table append-only (déjà : table `messages`)
   "ce qui a été DIT"              ← tout stocké, PAS tout relu

Couche 3 — INDEX SÉMANTIQUE    → DB vectorielle (PLUS TARD)
   "retrouver un détail enfoui"    ← RAG sur la couche 2, quand l'historique est long
```

### 9.2 Les deux mécanismes clés (Phase 3)

- **Extraction de mémoire** : après chaque échange (ou périodiquement), un appel LLM extrait les infos utiles de la conversation et fait un **upsert dans les tables structurées** (couche 1). Le coach lit ces tables, pas tout l'historique.
- **Résumé glissant** : un petit résumé évolutif (200-400 mots) du profil/contexte, réécrit régulièrement et injecté à chaque tour. Simple, lisible, et souvent **plus efficace qu'un vectoriel** pour ce use-case (capture le "feeling" de la relation).

### 9.3 Quand ajouter le vectoriel (couche 3)

Seulement quand : (a) l'historique devient long (mois de discussion) ET (b) on veut du rappel sémantique fin. On indexe alors la couche 2 et on fait du RAG **en complément** des faits structurés. Coût + complexité en plus → à n'ajouter que sur besoin réel.

### 9.4 Ordre

```
MAINTENANT   Couche 1 (structuré) + Couche 2 (déjà fait)
             + extraction de mémoire + résumé glissant
PLUS TARD    Couche 3 (vectoriel) quand l'historique sera long
```

---

## 10. Backlog — idées à ne pas perdre

> Toute idée qui n'est pas implémentée tout de suite atterrit ICI pour ne pas la perdre. Statut : ⬜ à faire · 🔶 en cours · ✅ fait.

### Features produit

- ⬜ **Module alimentation / nutrition** (dédié, plus tard) : table alimentation, **calories de maintien (TDEE)**, macros, suivi des repas, photos de repas. Pour l'instant l'alimentation est captée grossièrement dans `facts` ; on ne détaille pas.
- ⬜ **Développement progressif de la relation** : grades **recrue → soldat → chef → frère d'armes** (un `relationship_level` trackable = ancienneté + régularité + rechutes surmontées). Débloque progressivement le comportement du Sergent.
- ⬜ **Dévoilement progressif du passé du Sergent** : sa blessure intime / son vécu de guerre ne se révèlent QU'À haut niveau de confiance (gated par le `relationship_level`). ⚠️ Actuellement **verrouillé** dans la persona (il n'en parle jamais). À débloquer avec les grades.
- ⬜ **Moteur proactif** : rappels de séance (avant + débrief après), prise de news auto sur `events`, relances si inactif. ⚠️ contrainte WhatsApp fenêtre 24h / templates Meta.
- ⬜ **Rapport du soir** : débrief quotidien du Sergent (journée moyenne / ratée / bonne) — via le moteur proactif.
- ⬜ **Détection de patterns** : le Sergent repère les schémas ("quand tu dors mal, tu pars en vrille") — analyse sur l'historique/events.
- ⬜ **Résumé glissant** (mémoire) : la "fiche" du user en langage naturel, injectée à chaque tour.
- ⬜ **Curseurs de personnalité** (humour, fermeté, implication…) — surtout utile quand on rouvrira le multi-coach.
- ⬜ **Réactiver le casting multi-coachs** (baba, glam, bienveillant, intello) + matching + Head Coach — on est en mono-coach (le Sergent) pour l'instant.

### Programme / entraînement

- ⬜ **Enrichir la bibliothèque de templates** (au-delà du seul `fullbody_debutant_3x`) + **liste d'exos avec alternatives** (pour swaps propres en cas de blessure).
- ⬜ **Faire relire les templates par un coach diplômé** avant prod.

### Mémoire / data

- ⬜ **DB vectorielle** (couche 3) : rappel sémantique fin, quand l'historique sera long.

### Infra / business

- ⬜ **Hébergement en ligne** (Railway/Render/Fly) : URL fixe, tourne H24 (fin du cirque des tunnels).
- ⬜ **WhatsApp Business officiel** + templates approuvés Meta (pour le proactif hors fenêtre 24h).
- ⬜ **Validation signature Twilio** sur le webhook (sécurité) avant prod.
- ⬜ **Monétisation** : page web + Stripe (premiers €), puis app native (dashboard + acquisition).
