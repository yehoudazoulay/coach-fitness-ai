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
   LES BRIQUES DE CONTENU (mêmes niveau) :
     1. Personnalité coach     4. Santé (sommeil, médical, compléments)
     2. Alimentation           5. Events (blessures ponctuelles, vie...)
     3. Programme gym          6. Suivi / progression / adhérence  ⭐
                               7. Objectifs & jalons
                                                 │
        ┌──────────────────── FONDATIONS (le socle) ───────────────────────────────┐
        │   🧠 MÉMOIRE (le cerveau qui relie tout)   ·   🛡️ SÉCURITÉ & ÉTHIQUE       │
        │                                              (garde-fous transversaux)     │
        └──────────────────────────────────────────────────────────────────────────┘
```

Principe : les **briques** = les domaines (au même niveau). Le **moteur de relances** =
transversal (une seule logique, pas dupliquée). Les **fondations** = sous tout le reste.
⚠️ Ne pas confondre la **brique Santé** (le domaine : données, sommeil, compléments) et la
**fondation Sécurité & éthique** (les règles/garde-fous qui protègent, notamment, cette brique).

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

### 🛡️ Sécurité & éthique — garde-fous transversaux · 🔶

Les *règles* qui s'appliquent partout (à ne pas confondre avec la brique Santé, qui est le
*domaine*). Critique pour une app de santé.
- ✅ Garde-fous dans la persona (pas médecin, pas d'entraînement blessé, pas minceur=
  valeur, pas de comportements extrêmes, pas de remplacement d'aide médicale/psy…).
- ⬜ Garde-fous **alimentation & santé** (TCA, restrictions dangereuses, pas de diagnostic,
  pas de dosage précis de compléments) — à durcir avec ces briques.
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

### 4. Santé · ⬜ (sensible — plus tard, avec soin)

Le domaine santé au sens large (≠ alimentation, ≠ events ponctuels). C'était **l'idée
d'origine** du projet (analyses sanguines → compléments). **Brique la plus sensible** du
produit (quasi-médical).
- ⬜ **Bien-être quotidien** : sommeil (qualité/durée), énergie, stress, moral — ces
  signaux modulent l'entraînement (fatigue → mode infirmerie, etc.).
- ⬜ **Données médicales / analyses** : upload d'analyses sanguines, bilans → lecture et
  mise en contexte (⚠️ JAMAIS de diagnostic).
- ⬜ **Compléments alimentaires** : recommandations selon analyses/objectifs (⚠️ zone
  sensible : disclaimers, jamais de dosage précis, orienter vers un pro de santé).
- ⬜ **Conditions & limitations médicales** : pathologies, contre-indications, blessures
  chroniques → contraintes fortes pour le programme et l'alimentation.
- 🛡️ Encadrée strictement par la fondation Sécurité & éthique. Idéalement relue par un pro
  de santé avant toute mise en prod.

### 5. Events (blessures ponctuelles, vie...) · ✅

Le mécanisme de mémoire **épisodique** (≠ brique Santé, qui est le domaine ongoing).
- ✅ Table `events` en SCD2 : statut qui évolue (malade→amélioration→résolu). Blessure
  ponctuelle, perso, boulot, moral, victoire. Prise de news, adaptation du programme.

### 6. ⭐ Suivi / progression / adhérence · 🔶 (LA brique de rétention)

Ce que l'utilisateur FAIT vraiment (≠ ce que le coach dit/sait). **Le cœur pour une
audience qui abandonne** — et la source de presque toutes les relances.
- ✅ **Adhérence** : table `workouts` (séances faites, ressenti, notes) + calcul
  `sessions_this_week` vs objectif (`frequence`) + dernière séance. Injecté au coach.
- ✅ **Capture conversationnelle** : "j'ai fait ma séance jambes" → loggé auto (via
  `update_memory`, sans double-comptage).
- 🔶 **Progression** : mesures (`measurements`) + tendance poids injectée. ⬜ perfs
  détaillées (charges/reps par exo), ⬜ photos.
- ⬜ Suivi de la bouffe (avec la brique Alimentation).
- Alimente : débriefs de séance, félicitations, relances — et le futur moteur proactif.

### 7. Objectifs & jalons · 🔶

- ✅ `goals` : objectifs + motivations (le "pourquoi", levier n°1).
- ✅ **Jalons / échéances** : table `milestones` (label + date), captés auto, compte à
  rebours injecté au coach ("mariage dans N jours"). Moteur de motivation.
- ⬜ Progression vers le jalon (où on en est vs l'objectif).

---

## Le moteur transversal de relances / triggers · 🔶

**Une seule logique**, pas dupliquée par brique. Il pioche dans toutes les briques pour
décider : **quand** relancer, et **quoi** dire. Socle : `scheduler.py` (tick /5 min) +
`generate_proactive()` (message dans la voix du coach) + `planned_sessions`.

Triggers :
- ✅ **Rappel avant séance** (+ quoi faire) & **débrief après** ("alors ? c'est quand la
  prochaine ?"). Boucle auto-entretenue.
- ✅ **Events** : prise de news sur santé/blessure/moral non résolu ("ça va mieux le genou ?").
- ✅ **Suivi/adhérence** : relance si inactif ("zéro séance, c'est quand la prochaine ?").
- ✅ **Jalons** : compte à rebours quand le jalon est proche (≤ 90 j).
- ⬜ Alimentation : "t'as pensé à ta prise de protéines ?" (plus tard)

Anti-spam : `proactive_log` + cooldowns (news 72h, inactivité 48h, jalon 7j) ; 1 relance
conditionnelle max par utilisateur par tick, par priorité (news > inactivité > jalon).

⚠️ **Contraintes réelles** : (1) WhatsApp — envoi proactif hors fenêtre 24h = templates Meta
(prod, pas sandbox) ; un envoi refusé n'est pas marqué envoyé → retenté. (2) Render free —
le service **s'endort** après 15 min → le scheduler ne tourne QUE quand le service est
éveillé. Pour du proactif fiable : always-on (payant) ou keep-alive.

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
5. ⬜ **Alimentation + Santé** (briques sensibles : garde-fous renforcés, pas de
   diagnostic/dosage, relecture par un pro de santé)
6. ⬜ Sortie du sandbox (WhatsApp Business) + always-on + RGPD → vrais users
7. ⬜ Monétisation (web + Stripe, puis app native)
