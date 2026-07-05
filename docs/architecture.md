# Architecture du produit — vue d'ensemble

> La carte du projet : les fondations (socle), les briques de contenu, le moteur
> transversal de relances/triggers, et la relation dans le temps. Statut : ✅ fait ·
> 🔶 partiel · ⬜ à faire.
> Voir aussi : [brainstorm.md](brainstorm.md) (backlog §10), [sergent_bible.md](sergent_bible.md).
> Dernière maj : 2026-07-05

---

## Schéma d'ensemble

```
                         ┌───────────────────────────────────────────┐
                         │        UTILISATEUR  (via WhatsApp)         │
                         └───────────────────────┬───────────────────┘
                                                 │
        ┌────────────── MOTEUR DE RELANCES / TRIGGERS (transversal) ───────────────┐
        │   pioche dans TOUTES les briques : quand relancer ? quoi dire ?           │
        └───────────────────────────────────────┬──────────────────────────────────┘
                                                 │
   ┌─────────────┬─────────────┬────────────┬───┴────────┬──────────────┬─────────────┐
   │ 1. PERSO    │ 2. ALIMEN-  │ 3. PROGRAMME│ 4. EVENTS  │ 5. SUIVI /   │ 6. OBJECTIFS│
   │    COACH    │    TATION   │    GYM      │ (blessures,│  PROGRESSION │  & JALONS   │
   │             │             │             │  vie...)   │  / ADHÉRENCE │             │
   └─────────────┴─────────────┴────────────┴────────────┴──────────────┴─────────────┘
                                                 │
        ┌──────────────────── FONDATIONS (le socle) ───────────────────────────────┐
        │   🧠 MÉMOIRE (le cerveau qui relie tout)   ·   🛡️ SÉCURITÉ / SANTÉ         │
        └──────────────────────────────────────────────────────────────────────────┘
```

Principe : les **briques** = les domaines. Le **moteur de relances** = transversal (une
seule logique, pas dupliquée). Les **fondations** = sous tout le reste.

---

## Fondations (le socle)

### 🧠 Mémoire — le cerveau qui relie tout · ✅ (base) / 🔶 (à compléter)

Ce qui fait que le coach "te connaît" à travers toutes les briques.
- ✅ `goals` (objectifs + motivations), `facts` (quotidien), `events` (SCD2, statut),
  `measurements` (série temporelle), `programs` (SCD2). Routage auto (`update_memory`).
- ✅ Date du jour injectée. ✅ Injection dans le system prompt.
- ⬜ **Résumé glissant** (la "fiche" du user en langage naturel).
- ⬜ **Détection de patterns** ("quand tu dors mal, tu pars en vrille").
- ⬜ Vectoriel (couche 3) quand l'historique sera long.

### 🛡️ Sécurité / santé — garde-fous · 🔶

Critique pour une app de santé (et surtout quand on ajoutera l'alimentation).
- ✅ Garde-fous dans la persona (pas médecin, pas d'entraînement blessé, pas minceur=
  valeur, pas de comportements extrêmes, pas de remplacement d'aide médicale/psy…).
- ⬜ Garde-fous **alimentation** (TCA, restrictions dangereuses) — à durcir avec la brique.
- ⬜ Conformité **RGPD** (données de santé) dès de vrais users.
- ⬜ Validation signature Twilio (webhook).

---

## Les briques de contenu

### 1. Personnalité coach · ✅

Le Sergent (bible : [sergent_bible.md](sergent_bible.md)). Anti-guerre, discipline>
motivation, modes tribunal/infirmerie, recadrages (guerre, ego), Chef/Soldat.
- ✅ Persona + découverte + parcours de mise en place.
- ⬜ **Grades relationnels** (recrue→soldat→chef→frère d'armes) + dévoilement progressif
  du passé (verrouillé pour l'instant). *Cross-transversal : fait évoluer cette brique
  dans le temps.*
- ⬜ Curseurs (humour/fermeté…) — surtout utile si on rouvre le multi-coach.

### 2. Alimentation · ⬜ (plus tard)

- ⬜ Table dédiée : repas, macros, **calories de maintien (TDEE)**, photos de repas.
- ⬜ Conseils nutrition adaptés (objectif, contraintes) + garde-fous TCA.
- Pour l'instant : capté grossièrement dans `facts`, on ne détaille pas.

### 3. Programme gym · ✅

- ✅ Approche hybride : templates experts adaptés par le LLM (dispos, blessures, matériel).
- ✅ Proposé/validé en mise en place, ou apporté par l'utilisateur. Stocké en SCD2
  (adaptable : blessure → nouvelle version). Planning fixe ou flexible.
- ⬜ Enrichir la bibliothèque de templates + liste d'exos avec alternatives.
- ⬜ Faire relire par un coach diplômé avant prod.

### 4. Events (blessures, vie...) · ✅

- ✅ Table `events` en SCD2 : statut qui évolue (malade→amélioration→résolu). Santé,
  blessure, perso, boulot, moral, victoire. Prise de news, adaptation du programme.

### 5. ⭐ Suivi / progression / adhérence · 🔶 (LA brique de rétention)

Ce que l'utilisateur FAIT vraiment (≠ ce que le coach dit/sait). **Le cœur pour une
audience qui abandonne** — et la source de presque toutes les relances.
- 🔶 **Mesures** (`measurements`) : poids, tours, taux de gras… (base posée).
- ⬜ **Adhérence** : séances faites vs prévues, régularité, suivi de la bouffe.
- ⬜ **Progression visible** : montrer les résultats ("+2 cm de bras en 6 semaines",
  courbe de poids, perfs qui montent) — ce qui donne envie de rester.
- ⬜ **Photos** de progression.
- Alimente : les débriefs de séance, les félicitations, les relances de recadrage.

### 6. Objectifs & jalons · 🔶

- ✅ `goals` : objectifs + motivations (le "pourquoi", levier n°1).
- ⬜ **Jalons / échéances** : la deadline (ex : mariage le 7 fév) → urgence et compte à
  rebours dans les relances ("plus que 5 semaines, Soldat"). Moteur de motivation fort.
- ⬜ Progression vers le jalon (où on en est vs l'objectif).

---

## Le moteur transversal de relances / triggers · ⬜

**Une seule logique**, pas dupliquée par brique. Il pioche dans toutes les briques pour
décider : **quand** relancer, et **quoi** dire.

Exemples de triggers (par brique) :
- Programme : rappel avant séance (+ quoi faire) · débrief après ("alors ?")
- Events : prise de news ("ça va mieux le genou ?") · relance si malade depuis X jours
- Suivi/adhérence : "t'as fait combien de séances cette semaine ?" · relance si inactif
- Jalons : compte à rebours ("plus que N semaines avant le mariage")
- Alimentation : "t'as pensé à ta prise de protéines ?" (plus tard)

⚠️ **Contrainte WhatsApp** : écrire en premier hors fenêtre 24h nécessite des **templates
Meta** (compte Business, pas le sandbox). En sandbox : marche seulement si l'utilisateur
a écrit < 24h. → le moteur se construit maintenant, tourne à fond en prod.

Techniquement : le scheduler (`app/scheduler.py`, APScheduler) est en place, désactivé
par défaut. C'est le point d'ancrage du moteur.

---

## Ordre de construction conseillé

1. ✅ Perso + programme + events + mémoire de base (FAIT)
2. 🔶 **Suivi / progression / adhérence** (LA rétention) + **jalons** — prochaine priorité
3. ⬜ **Moteur proactif** (relances/triggers) — exploite 1 & 2
4. ⬜ Grades relationnels + dévoilement progressif
5. ⬜ Alimentation (brique + garde-fous)
6. ⬜ Sortie du sandbox (WhatsApp Business) + always-on + RGPD → vrais users
7. ⬜ Monétisation (web + Stripe, puis app native)
