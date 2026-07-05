# App mobile — Le Sergent (Expo / React Native)

Chat avec le coach + dashboard de suivi. Consomme l'API du backend (Render).
Un seul code → iOS + Android (+ web).

## Prérequis (une fois)
- **Node.js** installé sur ton PC : https://nodejs.org
- **Expo Go** sur ton téléphone (App Store / Play Store)

## Lancer (pour tester)
```bash
cd mobile
npm install
npx expo start
```
Un **QR code** s'affiche → ouvre **Expo Go** sur ton tél et scanne-le.
L'app tourne sur ton téléphone, en live (elle recharge à chaque modif du code).

> Sur PC uniquement : `npx expo start --web` ouvre l'app dans le navigateur.

## Config
En haut de `App.js` :
- `API_URL` = URL de ton backend Render (déjà réglée sur coach-fitness-ai.onrender.com)
- `USER` = ton identifiant de test (ex. `app:yehouda`)

## Notes
- Le backend Render free s'endort après 15 min → le 1er appel peut mettre ~30-60s
  (le service se réveille), puis c'est fluide.
- Si `npm install` râle sur les versions, lance `npx expo install --fix`.
