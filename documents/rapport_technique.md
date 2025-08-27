# 📑 Rapport technique – IMDB Sentiment Analysis

## 1. Méthodes

### 1.1 Objectif

Développer un classificateur de critiques de films (positives / négatives) sur le dataset **IMDB Reviews**, avec :

-   une baseline simple (TF-IDF + régression logistique),
    
-   un modèle avancé basé sur **DistilBERT fine-tuned avec LoRA** (Parameter-Efficient Fine-Tuning).
    

L’accent a été mis sur :

-   la reproductibilité (gestion des seeds, structure claire),
    
-   l’explicabilité (LIME + attention visualization),
    
-   l’engineering (gestion des fichiers, API FastAPI, logging).

Le projet est conçu comme un environnement de test pour différents modèles avec une configuration par défaut (pour la simplicité) mais modulable.
Tous les fichiers générés (modèles, résultats, rapports) sont facilement identifiables grâce au système de "model_id".

----------

### 1.2 Pipeline global

1.  **Chargement / prétraitement des données**
    
    -   Dataset : `imdb` via Hugging Face Datasets.
        
    -   Split train/test.
        
    -   Nettoyage minimal (tokenisation gérée par le tokenizer de Hugging Face).
        
2.  **Baseline : TF-IDF + Logistic Regression**
    
    -   Vectorisation avec `TfidfVectorizer`.
        
    -   Classification avec `LogisticRegression`.
        
    -   Sauvegarde via `joblib`.
        
3.  **Modèle LoRA : DistilBERT**
    
    -   Modèle de base : `distilbert-base-uncased`.
        
    -   Ajout d’une tête de classification binaire.
        
    -   Fine-tuning avec **PEFT LoRA** (modules `q_lin`, `v_lin`).
        
    -   Entraînement via `Trainer` (Hugging Face).
        
    -   Sauvegarde complète du modèle + tokenizer + résultats.
        
4.  **Évaluation**
    
    -   `classification_report` de scikit-learn.
        
    -   Échantillons custom si besoin (`--npreds`).
        
5.  **Explicabilité**
    
    -   **LIME** : met en évidence les tokens influents pour une prédiction.
        
    -   **Attention rollout** : agrège les matrices d’attention pour visualiser l’importance des tokens.
        
6.  **API FastAPI**
    
    -   Endpoint `/predict` pour interroger les modèles.
        
    -   Retourne la prédiction (`label`) et les probabilités.
        

----------

## 2. Résultats

### 2.1 Baseline (TF-IDF + LogReg)

-   Accuracy autour de **85%** sur le jeu de test.
    
-   Avantage : rapide, interprétable, peu coûteux.
    
-   Limite : sensible au vocabulaire, ne capture pas les dépendances contextuelles.
    

### 2.2 LoRA (DistilBERT)

-   Après fine-tuning 10 epochs : accuracy autour des **93%** sur IMDB.
    
-   Avantage : capture les relations contextuelles complexes.
    
-   Limite : entraînement plus coûteux (GPU nécessaire).
    

### 2.3 Explicabilité

-   **LIME** : montre que des mots très polarisants (ex: _“excellent”_, _“awful”_) pèsent fortement dans la décision.
    
-   **Attention rollout** : permet de visualiser quels tokens influencent le plus la prédiction du modèle transformer.
    

----------

## 3. Limitations et axes d’amélioration

### 3.1 Limitations

-   LoRA ne met à jour qu’une petite partie des poids; gain en efficacité mais perte possible en performance vs full fine-tuning.
        
-   Baseline performante mais incapable de généraliser hors IMDB (vocabulaire spécifique).
    
- Ne fonctionne qu'en anglais


### 3.2 Améliorations possibles

-   Tester d’autres modèles (RoBERTa, DeBERTa, ...). 

-  Toutes les données d'entrainements (configs + results) sont actuellement sauvegardées indépendamment.
Etre capable de les centraliser (dans un .csv par exemple) et de les comparer serait une excellente prochaine étape.

-  Environnement de DATA plus poussé 
	- Tracabilité des données utilisées avec "Data Version Control"
	- Ajout de nouvelles database / features 
    
-   Explorer d’autres techniques d’explicabilité (SHAP, Integrated Gradients).
    
-   Déployer le modèle avec Docker pour un usage plus simple.
    
-   Évaluer la robustesse (textes courts, fautes de frappe, adversarial examples).
