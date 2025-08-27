# Question 1 : génération de descriptions d'armes RPG 


### 1) Problème & contraintes

-   **Entrée** : Métadonnées 
	- Type
	- Rareté
	- Univers
	- Statistiques de l'arme
    
-   **Sortie** : une description texte courte, cohérente avec l’univers et homogène stylistiquement.
    
-   **Données** : 500 descriptions existantes (peu), 2000+ armes à couvrir.
    
-   **Contraintes clés** : 
	- Cohérence de style 
	- Absence de contradictions avec les stats
	- Intégration dans le pipeline **Unity** (pré-build/éditeur)
	- Peu de données initiales : 500 exemples est assez faible. S'il y a une grande variance dans les métadonnées (beaucoup de type d'armes, de statistiques, ...), ou tout simplement que ces données ne sont pas représentatives (e.g. ne contient que des épées) il sera compliqué de ré-entrainer des modèles d'IA.



### 2) Approches

#### Option A. Règles pures (grammaires, listes, accords)

**Idée** : assembler des phrases à partir de gabarits + dictionnaires, avec règles d’accord/variantes.

-   **+** : déterministe, très rapide, coût nul à l’inférence, facile à auditer, aucun risque de “lore drift”.
    
-   **–** : répétitif, peu de variété, coûteux à maintenir quand l’univers grandit, impossible d'avoir une expérience immersive.
    
-   **Quand l’utiliser** : baseline robuste, ou si la direction artistique veut un style _très_ cadré.
    

#### Option B. Templates paramétrés (+ micro-variation)

**Idée** : gabarits Jinja2 + banques de formulations, règles d’inflexion (sing/pluriel, genre), thésaurus limité, contraintes de longueur.

-   **+** : qualité stable, plus de variété que A, facile à forcer la mention de stats, très rapide.
    
-   **–** : style parfois “mécanique”, effort initial de rédaction des gabarits, risque d’usure sur 2000+ items.
    
-   **Quand l’utiliser** : livraison rapide avec contrôle fort ; excellent socle combinable avec un modèle (voir D).
    

#### Option C. Modèles génératifs “promptés” (sans fine-tuning)

**Idée** : LLM open-source (7–8B) en local, _few-shot_ avec 20–50 exemples représentatifs + _system prompt_ (charte de style), **constrained decoding** (longueur, lexique).

-   **+** : mise en place rapide, style plus naturel, bonne diversité, pas de coût/risque de training.
    
-   **–** : avec 500 exemples non utilisés en fine-tuning, le modèle peut ignorer des conventions métier ; cohérence et factualité à surveiller ; non déterministe sans garde-fous.
    
-   **Quand l’utiliser** : POC/mode “rédacteur assisté”, ou première version avant fine-tuning.
    

#### Option D. Modèles génératifs **fine-tunés** (PEFT/LoRA)

**Idée** : encoder les métadonnées + **LoRA** avec une entrée structurée (ex: json) et des **tokens de contrôle** (style, univers, rareté).

-   **+** : style homogène, meilleure obéissance aux contraintes, latence locale raisonnable, coût unitaire bas, confidentialité des données.

-   **–** : 500 échantillons = peu → risque d’overfit ; nécessite _data cleaning_ + éventuelle **augmentation** (paraphrases) ; MLOps nécessaires.

-   **Quand l’utiliser** : cible “production” quand la qualité/consistance priment et qu’on veut éviter API externes.
    

#### Option E. RAG (Retrieval-Augmented Generation) sur banque d’exemples & charte de style

**Idée** : indexer les 500 descriptions + une **charte éditoriale** ; au moment de générer, récupérer 3–5 plus proches (même type/rareté/univers) + règles de style, puis _prompt_ le LLM.

-   **+** : profite directement du style existant, peu de données requises, facilement extensible par les narrative designers.
    
-   **–** : dépendance à la qualité des exemples ; sans contraintes, peut “copier” trop près ; latence ↑ (retrieval).
    
-   **Quand l’utiliser** : excellente passerelle entre C et D ; forte cohérence de style dès peu de données.
    

## 4) Recommendations

### La solution la plus performante : RAG (E) + LLM fine-tuné (D)

L'option *idéale* en terme d'efficacité serait un Hybride entre l'option (E) et (D) : fine-tuner un petit modèle (option D) pour les structures et laisser le RAG injecter le style/lore (option E).

Cependant la contrainte principale est le manque de données initiales (500) qui peut être handicapant dans le fine-tuning. De plus, cette option augmente la complexité et le coût initial en temps humain. Si la quantité d'armes restantes à décrire (1500+) n'est pas vouée à évoluer, il est préférable de préconiser une solution plus simple. 

### La solution la plus adaptée : RAG (E) + LLM (C\)

Commencer par combiner les options (E) et (C\), c'est à dire un LLM conditionné, recevant un prompt structuré dans un contexte RAG (e.g. systématiquement recontextualiser les données envoyées avec des données similaires existantes) couplé à une vérification/correction humaine.

Lorsque le dataset sera suffisamment fournit, et si le **besoin** s'en fait sentir, fine-tunner un LoRA.

## 4) Architecture

### Vue d’ensemble (offline → online)

1.  **Données & style**
    
    -   Normaliser les 500 descriptions (nettoyage, longueur cible, variables récurrentes).
        
    -   Rédiger une **Charte éditoriale** (ton, tense, interjections permises, longueur, vocabulaire interdit/autorisé, mentions obligatoires par type).
        
    -   Annoter quelques exemples de tests (50 - 100).
        
2.  **Génération**
    
    -   **Étape 1 – Sémantique** (toujours vraie) : Template paramétré produit un **brouillon** fidèle aux stats (B).
        
    -   **Étape 2 – Stylisation** :
        -   Phase 1 (rapide) : 
	        - **LLM** _instruct_ local (C\) (respect des metadata) 
	        - **RAG** (E) avec 3–5 exemples proches (metadata similaires)
	        - **Constrained decoding** : longueur 40–80 mots, vocabulaire bannis/obligatoires, ... (= Chartre Editoriale)
            
        -   Phase 2 (si besoin) : **fine-tuning LoRA** (D) pour réduire la variance et stabiliser le résultat.
            
3.  **Validation automatique**
    
    -   **Règles** : regex/parseur pour vérifier
        
        -   mentions requises (élément, type, rareté) ;
            
        -   absence de mots interdits ;
            
        -   limite de longueur ;
            
        -   cohérence stat : texte (ex. si `element=fire` alors présence d’un champ lexical feu).
            
    -   **Classifieurs** légers :
        
        -   style (binaire : “conforme / non conforme”) ;
            
        -   Garde fou de certaines dérives aberrantes (e.g : injures, hors sujet par rapport au lore, ...)
            
    -   **Détecteurs de similarité** (cosine embeddings) pour éviter répétitions/near-duplicates.
        
4.  **Servir & intégration Unity**
    
    -   **Offline (recommandé)** : pré-générer toutes les descriptions en contenu éditorial (évite dépendance réseau à l’exécution).
        
    -   **Service** : **FastAPI** + pipeline HF sous **Docker** ; endpoint `/generate` (Body: métadonnées -> Output: description) exposé seulement aux outils d’édition (Unity Editor tool).
        
    -   **Unity** : outil d’éditeur (C#) qui
        
        -   batch-génère depuis les ScriptableObjects (`WeaponData`);
            
        -   écrit dans les **Localization Tables** (facilitera la trad) ;
            
        -   propose UI d’acceptation manuelle et _diff_ textuel.
            
5.  **MLOps / CI-CD**

    -   **Versionner** données (DVC) + modèles
 
    -   **Tests** : unitaires (parse, decode), génération sur le "test set" d'items avec analyse des metrics (BERTscore, ...), tests de conformité. 

    -   **Gating** en CI : un build ne passe que si ≥ X% de validations automatiques + score style moyen ≥ seuil.

    -   **Images Docker** : base CPU et GPU ; _multi-stage build_ ; poids du modèle en artefacts.
        
    -   **Canary** : environnement “staging” pour que les narrative designers _valident par lot_ avant push vers prod (pré-génération).


## 5) Évaluation (automatique & humaine)

### Automatique (à chaque PR/build)

-   **Vérifs de contenu** (règles) : longueur, champs obligatoires, lexique interdit, cohérence stats, mots-clés.
    
-   **StyleScore** (classifieur) : petit modèle (LogReg/Small BERT) entraîné à distinguer _conforme / non conforme_ sur les 500 + exemples négatifs synthétiques.

-   **Similarité** : cosine vs corpus existant (seuil pour éviter la redite).
    
-   **Lisibilité** : bornes de complexité (phrases 10–22 mots, pas d’énumérations trop longues, ...)
    
-   **Mesures sémantiques** : 
	-   **BLEU / ROUGE / METEOR** : Vérifient la similarité entre le texte généré et une ou plusieurs références.
	        
	-   **BERTScore**: Compare la proximité sémantique (embeddings BERT) entre le texte généré et la référence.
	        
	-   **Perplexity (PPL)** : Mesure la “fluidité” du texte (à quel point la suite de mots est probable). Bon indicateur de cohérence linguistique, mais pas de l’adéquation à l’univers.
	        
	-   **Distinct-n** : Vérifie la diversité des n-grammes générés (évite que tous les textes se ressemblent trop).
    

### Humaine
Une excellente manière de qualifier le contenu généré par une IA (surtout dans ses débuts) est de quantifier le temps / énergie qu'il aura fallut à un humain pour "corriger" le résultat.
    
-   **Temps d’édition** : mesure du temps de retouche moyenne.

-   **Taux d’acceptation** : % descriptions acceptées sans retouche.

Il est également envisageable de demander à l'humain vérificateur de noter le travail de l'IA (_lisibilité_,  _cohérence_, ...)
