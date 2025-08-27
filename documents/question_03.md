# Question 03 - Outil Editeur & workflow

Décrivez comment vous concevriez un système d'outils d'éditeur Unity pour faciliter la création de contenu pédagogique par des non-programmeurs (level design, paramétrage d'objets, validation).

**Besoins :** Templates gameplay, paramétrage difficulté, intégration contenu, preview temps réel

**Contraintes :** Interface intuitive, RGPD, accessibilité WCAG, intégration LMS, formation users < 2h requise

**Livrable :** Architecture des outils, interfaces utilisateur, extensibilité, intégration workflow, et exemples concrets d'implémentation

## 1. Conception

Dans un premier temps, j’essaierais de **réduire au maximum la complexité de l’éditeur Unity** : plutôt que de leur demander d’aller fouiller dans l’Inspector et des centaines de paramètres, je leur créerais une **fenêtre dédiée** (genre _Content Designer_) avec des gros boutons clairs :

-   “Choisir un template de gameplay” (quiz, mini-jeu, escape room…).
    
-   “Ajuster la difficulté” avec un simple curseur ou menu déroulant.
    
-   “Ajouter du contenu” (texte, image, vidéo).
    

Ça serait ma première pierre : une interface simple et rassurante.

----------

Ensuite, je me pencherais sur la partie **preview**. Pour des gens qui ne programment pas, c’est hyper important de **voir tout de suite** ce qu’ils construisent. Donc j’ajouterais une zone de prévisualisation temps réel dans la fenêtre. 
Par exemple : changement de la couleur ou le niveau de difficulté, visualisation immédiate de l’effet (ou alors, un petit bouton _“Tester maintenant”_ qui lance une mini simulation).

----------

Une fois ça en place, je passerais au **contrôle qualité**. Parce que c’est bien de pouvoir créer, mais il faut aussi éviter les erreurs invisibles. Là, je mettrais un système de validation automatique :

-   Un onglet “Vérification” qui dit clairement si ton contenu est conforme (ex : “Couleur non lisible pour un daltonien”, “Vidéo sans sous-titre”, “Attention : champ personnel non RGPD”).
    
-   Avec des voyants rouges/verts pour que ce soit clair en un coup d’œil.
    
- Beaucoup de sécurité, tester un maximum de cas de figure. Je vais chercher à créer un contexte très *très* encadré quit à limiter leurs options.

----------

Quand la base est fonctionnelle, je réfléchirais à **l’export vers les plateformes d’e-learning** (Moodle, LMS, etc.). L’idéal serait un bouton _“Exporter en SCORM/xAPI”_. Comme ça, en un clic, le contenu est prêt à être intégré sans prise de tête technique.
A voir par la 

----------

Enfin, je garderais en tête la **formation utilisateur**. L’objectif, c’est que quelqu’un qui n’a jamais codé puisse s’en sortir en moins de 2h. Donc :

-   Beaucoup de tooltips et explications simples.
    
-   Des workflows guidés type assistant : _1. Choisir template → 2. Paramétrer → 3. Vérifier → 4. Exporter_.
    
## 2. Architecture

-   **Core framework (C# API invisible aux créateurs)**
    
    -   Gestion des **templates gameplay** (ex : quiz interactif, escape room, serious game).
        
    -   Système de **paramétrage modulaire** (difficulté, objectifs pédagogiques, timers).
        
    -   Composants de **validation automatique** (tests d’accessibilité, cohérence des règles, RGPD compliance).
        
-   **Éditeur custom Unity**
    
    -   Fenêtres et Inspectors sur-mesure (EditorWindow, CustomPropertyDrawer).
        
    -   **WYSIWYG / Preview** pour voir le rendu sans lancer Play Mode.
        
-   **Extensibilité par ScriptableObjects**
    
    -   Les paramètres (par ex. “Difficulté facile/moyen/difficile”) sont stockés en **ScriptableObjects** - faciles à éditer sans code.
        
    -   Ces assets peuvent être partagés entre plusieurs scènes.

## 3. Extensibilité

-   **Ajout facile de nouveaux templates** :
    
    -   Chaque template est un **Prefab + ScriptableObject**.
        
    -   Pour créer un nouveau type de contenu (ex : puzzle, mini-labo virtuel), le développeur n’a qu’à fournir un prefab annoté.
        
    -   L’éditeur détecte automatiquement les nouveaux templates.
        
-   **Paramètres custom** :
    
    -   Système générique de _Property Drawers_ : un non-programmeur voit un champ lisible (“Durée en minutes”) plutôt qu’un float brut.
        
-   **Validation extensible** :
    
    -   `IValidationRule` interface C# : n’importe quel dev peut coder une nouvelle règle (ex : vérifier que toutes les vidéos ont des sous-titres).
    
##  4. Exemples concrets d’implémentation

### Exemple 1 – Création d’un quiz

1.  L’enseignant ouvre la fenêtre _Content Designer_.
    
2.  Clique sur **“Ajouter Quiz”** -> prefab “QuizTemplate” apparaît dans la scène.
    
3.  Dans l’inspector simplifié :
    
    -   Ajoute 5 questions (texte + réponses).
        
    -   Définit la difficulté = “Moyen”.
        
4.  Lance **Preview** -> test direct dans l’éditeur.
    
5.  Validation -> “OK : couleurs conformes, RGPD check passed”.
    
6.  Export SCORM pour Moodle.
    

----------

### Exemple 2 – Paramétrage d’un mini-jeu éducatif

1.  Drag & drop d’un **Template Escape Room**.
    
2.  Onglet **Paramètres** :
    
    -   Timer : 5 minutes.
        
    -   Indices : activés.
        
    -   Difficulté IA = “Facile”.
        
3.  Validation : alerte : “Attention, contraste faible sur un objet clé”.
    
4.  Correction directe depuis la fenêtre.
    
5.  Preview live : simulation avec avatar virtuel.
----------


## Conclusion

En résumé, ma démarche serait :

1.  **Créer une interface simple** -> templates, paramètres essentiels.
    
2.  **Donner du feedback visuel immédiat** avec une preview.
    
3.  **Automatiser la validation** pour éviter erreurs d’accessibilité ou de RGPD.
    
4.  **Faciliter l’export** vers les plateformes utilisées par les enseignants.
    
5.  **Former très vite les utilisateurs** grâce à une interface intuitive et guidée.