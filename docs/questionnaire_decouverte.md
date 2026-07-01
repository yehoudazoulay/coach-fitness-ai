# Questionnaire de découverte

> Le parcours mené par le coach AVANT d'attribuer un profil. Posé en **conversation
> naturelle sur WhatsApp** (une question à la fois, relances adaptatives), pas un
> formulaire. Objectif : récolter les faits fitness ET calibrer le coaching.
>
> Voir [brainstorm.md](brainstorm.md) §2 et §5 pour le cadre.
> Dernière maj : 2026-06-30

---

## Principes de passation

- **Ton HUMAIN et DRÔLE** : c'est non négociable. La découverte doit donner l'impression de discuter avec un vrai pote attachant et marrant, pas de remplir un formulaire. Vannes, légèreté, naturel, réactions spontanées aux réponses ("ah ouais quand même 😅", "ok je vois le genre"). C'est ce qui crée l'attachement dès la première minute et fait baisser l'abandon.
- **Conversationnel** : le coach pose 1 question, écoute, rebondit, enchaîne. Pas de bloc de 10 questions d'un coup.
- **Mené par le HEAD COACH** : l'entretien n'est PAS conduit par une voix neutre, mais par un personnage à part entière — le **Head Coach** (le boss/fondateur du programme, cf. [coachs.md](coachs.md)). C'est lui qui accueille, fait passer l'entretien (humain + drôle), puis **attribue et présente** le coach dédié à la fin. Ton coach personnel n'apparaît qu'au moment du handoff (le "reveal").
- **Noyau court** (~10 questions) pour limiter l'abandon ; le reste s'enrichit au fil des échanges (cf. fork §7.2 du brainstorm).
- Chaque réponse alimente un **champ du profil** (couche 1 mémoire) + sert au **calibrage du style/curseurs/personnage**.

---

## BLOC A — Fitness & lifestyle (les faits)

### A1. Objectif principal
**Q :** « Pour commencer, c'est quoi ton objectif n°1 en ce moment ? (perdre du gras, prendre du muscle, te sentir mieux, être plus en forme, performer…) »
- **Calibre / alimente :** `objectif`
- **Science :** Goal-Setting Theory — un objectif spécifique structure tout le reste.

### A2. Le "pourquoi maintenant"
**Q :** « Et pourquoi maintenant ? Qu'est-ce qui fait que tu t'y mets là, précisément ? »
- **Calibre / alimente :** `declencheur` (le "why" profond)
- **Science :** Motivational Interviewing — faire émerger la motivation intrinsèque ; servira de levier dans les relances.

### A3. Point de départ
**Q :** « T'es plutôt où aujourd'hui niveau activité physique ? Jamais, de temps en temps, ou déjà régulier ? »
- **Calibre / alimente :** `niveau`, `stade_changement`
- **Science :** Modèle Transthéorique — situer le stade (contemplation → action) pour ne pas sur/sous-doser.

### A4. Disponibilité & contraintes
**Q :** « Combien de temps tu peux y consacrer par semaine, et t'as des contraintes à connaître ? (boulot, horaires, matériel, blessures…) »
- **Calibre / alimente :** `temps_dispo`, `contraintes`, `blessures`
- **Science :** réalisme du plan (Goal-Setting : atteignable) + sécurité.

### A5. Alimentation & hygiène de vie
**Q :** « Côté alimentation et sommeil, ça ressemble à quoi en ce moment ? Plutôt carré, chaotique, ou des trucs précis à signaler ? »
- **Calibre / alimente :** `alimentation`, `sommeil`, `lifestyle`
- **Science :** baseline pour le self-monitoring (BCT) ; identifie les leviers hygiène de vie.

---

## BLOC B — Psychologique (calibrage du coaching)

### B1. Réaction à l'échec
**Q :** « Quand tu rates une séance ou que tu craques, t'as plutôt besoin qu'on te remonte en douceur, qu'on te recadre un peu, ou qu'on dédramatise avec une vanne ? »
- **Calibre / alimente :** curseur `fermeté`, curseur `humour`
- **Science :** base du ton ; détecte la tolérance au registre ferme.

### B2. Source de motivation
**Q :** « Tu te bouges surtout pour toi — te sentir bien, progresser — ou pour un résultat visible / le regard des autres ? »
- **Calibre / alimente :** `focus_motivationnel` (promotion vs prévention), `type_motivation` (intrinsèque/extrinsèque)
- **Science :** SDT + Regulatory Focus — oriente la formulation des messages (viser un gain vs éviter une perte).

### B3. Besoin d'autonomie
**Q :** « Tu préfères qu'on te dise exactement quoi faire, ou qu'on te guide en te laissant décider ? »
- **Calibre / alimente :** `niveau_autonomie`
- **Science :** SDT (autonomie) — coach directif vs facilitateur.

### B4. Niveau d'implication souhaité
**Q :** « Tu veux que je sois bien présent — des rappels quasi quotidiens — ou plus léger, un check de temps en temps ? »
- **Calibre / alimente :** `niveau_implication` (fréquence des relances)
- **Science :** dosage de la proactivité ; évite la sur-sollicitation (cause n°1 de désabonnement).

### B5. Tolérance à la pression
**Q :** « Dernière : si je te mets un peu la pression, que je te challenge, ça te booste ou ça te bloque ? »
- **Calibre / alimente :** `tolerance_pression` → **autorise ou non** les registres ferme/militaire/culpabilisant
- **Science :** garde-fou SDT — n'active le registre contrôlant que pour ceux qui y répondent vraiment.

---

## Sortie : ce que la découverte produit + le "reveal" du coach

À la fin, deux choses se passent : on construit le profil structuré, ET on **fait naître le personnage du coach**.

### 1. Le profil utilisateur (données)

```
profil_utilisateur = {
  # Bloc A
  objectif, declencheur, niveau, stade_changement,
  temps_dispo, contraintes, blessures,
  alimentation, sommeil, lifestyle,
  # Bloc B
  focus_motivationnel, type_motivation, niveau_autonomie,
  niveau_implication, tolerance_pression,
  # Calibrage dérivé
  style_coach proposé (+ justification courte),
  curseurs: { humour, fermeté, implication, verbosité, familiarité, exigence_suivi },
}
```

### 2. Le matching avec un coach du casting ⭐

Le coach n'est PAS généré : il est **choisi dans le casting fixe** ([coachs.md](coachs.md)). Ce sont des personnages déjà écrits, avec prénom, nom, vie et personnalité forte. La découverte sert à **matcher l'utilisateur avec le coach qui lui correspond le mieux** (style + tolérance à la pression + autonomie + énergie…).

```
matching = {
  coach_id,         # le personnage retenu dans le casting (ex: "marco")
  justification,    # pourquoi ce coach colle à cette personne
  curseurs: { humour, fermeté, implication, verbosité, familiarité, exigence_suivi },
}
```

→ Seuls les **curseurs** sont personnalisés ; l'identité du coach (prénom, nom, perso, façon de parler) vient telle quelle de sa fiche.

**Le moment "reveal" / handoff** (point de bascule émotionnel) : après la dernière question, **le Head Coach attribue le coach** et fait les présentations, sur un ton **humain et drôle**. Puis le coach dédié prend le relais (premier message dans sa propre voix). Exemple (si le matching retient "Marco") :

> **Head Coach** : « Ok, je sais exactement qui il te faut 🔥 Je te présente **Marco**. Ancien rugbyman reconverti, gueulard mais un cœur énorme — le mec qui te charrie mais te lâche jamais. Je te laisse entre de bonnes mains 😉 »
> *(handoff)*
> **Marco** : « Salut toi 👊 Alors comme ça on veut [objectif] ? Parfait, j'adore. On va bien s'amuser… enfin, surtout toi 😏 »

L'utilisateur peut alors : **valider**, ou **demander un autre coach** au Head Coach (changer de personnage/style). Le genre suit le coach choisi. → puis `state = active`.

> 💡 À trancher (TODO) : si l'utilisateur veut "quelqu'un d'autre", on propose le 2e meilleur match, ou on laisse parcourir le casting ? Combien de coachs visibles ?

---

## À trancher / TODO

- [ ] **Algo de matching** : comment scorer un utilisateur vers un coach du casting (style + tolérance pression + autonomie + énergie…) ? Règles simples ou laissé au LLM ?
- [ ] **Casting** : écrire les fiches personnages dans [coachs.md](coachs.md) (combien au lancement : 3-4 bien faits)
- [ ] **"Quelqu'un d'autre"** : proposer le 2e match, ou laisser parcourir le casting ?
- [ ] **Ton de la découverte** : écrire/tester le prompt qui garantit le côté humain + drôle sans tomber dans le lourd
- [ ] Valider/raccourcir la liste (10 questions est-ce trop ? trop peu ?)
- [ ] Décider de l'ordre exact et des relances de secours si réponse vague
- [ ] Mapper chaque champ → colonnes SQLite (schéma `users` à étendre)
- [ ] Écrire le prompt qui pilote la découverte (mène la conversation + sait quand elle est "complète")
- [ ] Écrire l'extracteur qui transforme les réponses en `profil_utilisateur` structuré
- [ ] (Optionnel) faire relire la logique psy par un pro avant d'en faire un argument marketing
