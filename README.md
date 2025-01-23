# Projet 48h : Identifier une technologie pour une interface BMS

## Objectif du projet
L’objectif de ce projet est de développer une interface graphique nouvelle permettant de visualiser les informations envoyées via le bus CAN par un système de gestion de batterie (BMS). Ce projet devra être réalisé en 48 heures.

L’interface devra :
- Afficher les données essentielles :
    - Les tensions (cellules individuelles, batterie totale, minimum, maximum).
    - Les températures des sondes NTC.
    - Les états d’alarme.
    - Le numéro de série (SN) du BMS.
- Être compatible avec le matériel PeakCAN pour la communication CAN.
- Garantir un aspect de sécurité logicielle :
    - Le résultat final doit être un exécutable ou un programme compilé.
    - Les scripts sources ne doivent pas être directement consultables par le client.

---
## Contraintes techniques

- Technologie  
Vous êtes libres de choisir la technologie ou le framework pour l’interface graphique (PyQt, Tkinter, JavaFX, etc.), à condition qu’elle soit :
    - Compatible avec le matériel PeakCAN.
    - Exécutable sous Windows.
- Affichage
    - Adapter en fonction de la résolution et de la taille d'écran
- Aspect sécurité
    - Le produit final devra être compilé.
    - Le client ne doit pas avoir accès au code source (livraison d’un .exe ou autre format compilé).

- Visualisation des données
    - L’interface doit être claire et intuitive.
    - Les données doivent être mises à jour en temps réel ou quasi temps réel (selon les messages CAN reçus).

- Documentation  
Fournir une documentation basique expliquant :
    - Comment utiliser l’interface.
    - Les fonctionnalités principales.
    
---
## Gestion des trames CAN pour le BMS

Ce projet implémente un système de gestion des trames CAN pour un système de gestion de batterie (BMS). Les différentes trames gèrent des données comme les tensions, les températures, les états des alarmes, et d'autres informations essentielles au fonctionnement du BMS.

---

### Table des matières

- [Trames CAN](#trames-can)
  - [Trame 0x200 - Tensions (V1 à V4)](#trame-0x200---tensions-v1-à-v4)
  - [Trame 0x201 - Tensions (V5 à V8)](#trame-0x201---tensions-v5-à-v8)
  - [Trame 0x202 - Tensions (V9 à V12)](#trame-0x202---tensions-v9-à-v12)
  - [Trame 0x203 - Tension V13](#trame-0x203---tension-v13)
  - [Trame 0x204 - Températures (NTC)](#trame-0x204---températures-ntc)
  - [Trame 0x205 - Statistiques Batterie](#trame-0x205---statistiques-batterie)
  - [Trame 0x206 - Alarmes](#trame-0x206---alarmes)
  - [Trame 0x300 - Numéro de Série (SN)](#trame-0x300---numéro-de-série-sn)
  - [Trame 0x301 - Version HW / SW](#trame-0x301---version-hw--sw)
---

### Trames CAN

#### Trame 0x200 - Tensions (V1 à V4)

- **Description** : Contient les tensions des cellules 1 à 4, chacune encodée sur 2 octets.
- **Structure** :  
  ```
  Octet 0-1 : V4
  Octet 2-3 : V3
  Octet 4-5 : V2
  Octet 6-7 : V1
  ```
- **Exemple** :  
  ```
  [0x0F, 0xA0, 0x0F, 0x80, 0x0F, 0x60, 0x0F, 0x40]
  ```

#### Trame 0x201 - Tensions (V5 à V8)

- **Description** : Contient les tensions des cellules 5 à 8, chacune encodée sur 2 octets.
- **Structure** :  
  ```
  Octet 0-1 : V8
  Octet 2-3 : V7
  Octet 4-5 : V6
  Octet 6-7 : V5
  ```

#### Trame 0x202 - Tensions (V9 à V12)

- **Description** : Contient les tensions des cellules 9 à 12, chacune encodée sur 2 octets.
- **Structure** :  
  ```
  Octet 0-1 : V12
  Octet 2-3 : V11
  Octet 4-5 : V10
  Octet 6-7 : V9
  ```

#### Trame 0x203 - Tension V13

- **Description** : Contient la tension de la cellule 13.
- **Structure** :  
  ```
  Octet 0-2 : Réservé (0x00, 0x00, 0x00)
  Octet 3-4 : V13
  Octet 5   : Réservé
  ```

#### Trame 0x204 - Températures (NTC)

- **Description** : Contient les températures mesurées par les sondes NTC.
- **Structure** :  
  ```
  Octet 0-1 : Réservé ou données supplémentaires (0x00)
  Octet 2-3 : NTC3 (température 3)
  Octet 4-5 : NTC2 (température 2)
  Octet 6-7 : NTC1 (température 1)
  ```

#### Trame 0x205 - Statistiques batterie

- **Description** : Contient les statistiques globales des cellules de la batterie.
- **Structure** :  
  ```
  Octet 0-1 : Vpack
  Octet 2-3 : Vmin
  Octet 4-5 : Vmax
  Octet 6-7 : Vbatt
  ```
- **Calculs** :  
  - `Vpack` : Somme des tensions des cellules.
  - `Vmin` : Tension minimale parmi les cellules.
  - `Vmax` : Tension maximale parmi les cellules.
  - `Vbatt` : Valeur mesurée de la batterie.

#### Trame 0x206 - Alarmes

- **Description** : Indique l'état des alarmes sur 6 octets.
- **Structure** :  
  ```
  Octet 0 : Vmin (bit 0), Vmax (bit 1)
  Octet 1 : Tmin (bit 0), Tmax (bit 1)
  Octet 2 : Vbatt (bit 0), SN (bit 1)
  Octet 3-5 : Réservé
  ```

#### Trame 0x300 - Numéro de série (SN)

- **Description** : Contient le numéro de série du BMS.
- **Structure** :  
  ```
  Octet 0-7 : PN, SN ou code produit (ex: [0x6E, 0xCF, 0xF1, 0x00, 0x19, 0x01, 0x04, 0xDD])

  ```
#### Trame 0x301 - Version HW / SW

- **Description** : Cette trame indique la version matérielle (Hardware) et logicielle (Software) du BMS..
- **Structure** :  
  ```
  Octet 0-2 : Réservés (0x00)
  Octet 3-4 : Version Hardware (ex. 2.0)
  Octet 5-7 : Version Software (ex. 1.22.4)
  ```

---

### Contributions

Les contributions sont les bienvenues ! Veuillez suivre ces étapes :
1. Forkez le dépôt.
2. Faites vos modifications et créez une pull request.

---

### Système de Notation : Projet 48h - Interface CAN BMS

#### 1. Présentation (5 points)
**Critères évalués :**

- **Qualité de la communication orale (professionnel) (2 points)**  
Clarté de l’expression, cohérence dans l’explication des choix techniques, respect des règles de présentation professionnelle.

- **Qualité du support de présentation (professionnel) (2 points)**  
Esthétique, lisibilité, et organisation du support (slides, PDF, etc.).  
Inclusion de schémas, de graphes et de visualisations des flux CAN.

- **Utilisation du temps de parole (1 point)**  
Respect du temps alloué (10 minutes maximum).

#### 2. Proposition (12 points)
**Critères évalués :**

- **Stack technologique (3 points)**  
Pertinence du choix des outils pour le projet (frameworks graphiques, gestion CAN, etc.).

- **Gestion des données (3 points)**  
Organisation et structuration des données reçues via CAN.  
Correcte interprétation et affichage des trames.

- **Architecture et infrastructure (3 points)**  
Clarté et robustesse du code.  
Gestion des exceptions et sécurité.

- **Sécurité (3 points)**  
Interface compilée sans accès direct au code source.  
Protection contre d’éventuelles données CAN mal formées.

#### 3. Maquette et Fonctionnalité (10 points)
**Critères évalués :**

- **Cohérence avec la présentation (3 points)**  
Alignement entre ce qui a été présenté et la solution développée.  
Visibilité des différentes fonctionnalités mentionnées.

- **Interface graphique (5 points)**  
Intuitivité et esthétique.  
Affichage des tensions, températures, alarmes et numéro de série.

- **Compatibilité avec PeakCAN (2 points)**  
Démonstration fonctionnelle et correcte sur le matériel.

---
### Logiciel Conseillé

Pour envoyer et recevoir des trames CAN, il est recommandé d'utiliser **PCAN-View**, l’outil fourni par Peak-System.  
- **PCAN-View** permet de :
- Configurer facilement l’interface PeakCAN (PCAN-USB, PCAN-PCI, etc.).
- Envoyer et réceptionner des trames CAN en temps réel.
- Surveiller l’activité sur le bus CAN et déboguer les données échangées.

Vous pouvez également utiliser ce logiciel pour simuler ou tester l’envoi de trames à l’application BMS que vous développez.
