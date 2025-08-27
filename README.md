# 🎬 IMDB Sentiment Analysis

Ce projet implémente un système de classification de critiques de films (positives / négatives) basé sur :
- **Baseline** : TF-IDF + Régression Logistique
- **LoRA (PEFT)** : Fine-tuning de DistilBERT

Il inclut aussi :
- 📊 Outils d’évaluation
- 🔍 Explication locale avec LIME
- 👀 Visualisation des poids d’attention
- 🌐 API FastAPI pour la prédiction

---

## 📑 Index des livrables

Dans le dossier "documents/" se trouvent les livrables de ce projet et des questions techniques complémentaires.

## Questions techniques
- [Question 1 : génération de descriptions d'armes RPG](documents/question_01.md)  
- [Question 2 : pipeline de build et tests Unity](documents/question_02.md)  
- [Question 3 (bonus) : outils d'éditeur pédagogiques dans Unity](documents/question_03.md)  

## Projet IMDB – Analyse de sentiments
- [Notebook d’analyse exploratoire des données](documents/data_analysis_imdb.ipynb) :
Ce notebook comprend la partie analyse du dataset en Partie 1. Il se poursuit en partie avec l'entrainement d'un modèle Baseline (Partie 2), d'un LoRA (Partie 3) et une comparaison très simpliste de ces deux modèles (Partie 4). Le but était de refaire ce projet d'analyse de sentiments dans une version ultra simpliste "straight to the point".
- [Rapport technique – IMDB](documents/rapport_technique.md)  



## ⚙️ Installation & Setup

### 1. Créer l’environnement (Conda recommandé)
```bash
conda create -n imdb-sentiment python=3.11
conda activate imdb-sentiment
````

### 2. Installer les dépendances

```bash
pip install -e .
```

#### GPU config (optionnel mais recommandé)
Si vous voulez faire tourner vos modèles sur votre GPU et que votre config le permet (cuda >11.8) 
```bash
# Installez PyTorch avec CUDA si vous avez un GPU NVIDIA :
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
# ou pour CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```


---

## 📂 Structure du projet

```
IMDB-sentiment/
│
├─ src/                   # Code source
│   ├─ data/          	  # Methods de manipulation des données
│   ├─ training/          # Scripts d’entraînement
│   ├─ prediction/        # Évaluation, explications, visualisations
│   └─ utils/             # Gestion fichiers, erreurs, logs
│
├─ artifacts/             # Modèles sauvegardés (baseline & LoRA)
├─ reports/               # Rapports (LIME, logs)
├─ results/               # Résultats chiffrés
├─ configs/               # Configurations YAML
│
├─ pyproject.toml         # Déclaration des scripts exécutables
└─ README.md
```

---

## 🚀 Commandes disponibles

Les exécutables sont déclarés dans `pyproject.toml` et peuvent être lancés directement.

---

### 🎓 Entraînement baseline (TF-IDF + LogReg)

```bash
train_baseline [--model_id ID]
```

* **Description** : Entraîne un modèle baseline simple.
* **Paramètres** :

  * `--model_id` *(str, optionnel)* : identifiant du modèle (par défaut = généré automatiquement).

---

### 🎓 Entraînement LoRA (DistilBERT + PEFT)

```bash
train_lora [--epochs E] [--batch_size N] [--max_length L] [--lr LR] [--model_id ID]
```

* **Description** : Fine-tune DistilBERT avec LoRA.
* **Paramètres** :

  * `--epochs` *(int)* : nombre d’époques d’entraînement.
  * `--batch_size` *(int)* : taille des batchs (doit être >0, idéalement puissance de 2).
  * `--max_length` *(int)* : longueur max des séquences tokenisées.
  * `--lr` *(float)* : learning rate.
  * `--model_id` *(str, défaut: timestamp)* : identifiant unique du modèle.

---

### 📊 Évaluation d’un modèle

```bash
evaluate --model_type {baseline,lora} [--model_id ID] [--batch_size N] [--npreds K]
```

* **Description** : Évalue un modèle entraîné sur IMDB.
* **Paramètres** :

  * `--model_type` *(str)* : `baseline` ou `lora`.
  * `--model_id` *(str)* : identifiant du modèle (par défaut = dernier trouvé).
  * `--batch_size` *(int)* : taille des batchs de prédiction.
  * `--npreds` *(int, optionnel)* : limite du nombre d’exemples testés.

---

### 🔍 Explication locale (LIME)

```bash
explain --text "Your review here" --model_type {baseline,lora} [--model_id ID]
```

* **Description** : Génère une explication locale (LIME) pour un texte donné.
* **Paramètres** :

  * `--text` *(str)* : critique de film à expliquer.
  * `--model_type` *(str)* : `baseline` ou `lora`.
  * `--model_id` *(str)* : identifiant du modèle (par défaut = dernier trouvé).
* **Sortie** : un fichier HTML dans `reports/`.

---

### 👀 Visualisation des poids d’attention

```bash
attention --text "Your review here" [--model_id ID]
```

* **Description** : Visualise les scores d’attention du modèle.
* **Paramètres** :

  * `--text` *(str)* : critique de film.
  * `--model_id` *(str)* : identifiant du modèle (par défaut = dernier trouvé).

---

### 🌐 API FastAPI

```bash
start_api
```

* **Description** : Lance une API FastAPI pour prédire via HTTP.
* **Endpoints** :

  * `POST /predict`

    * **Body** :

      ```json
      {
        "text": "This movie was amazing!",
        "model_id": "latest"
      }
      ```
    * **Retour** :

      ```json
      {
        "label": "pos",
        "probs": {"neg": 0.12, "pos": 0.88}
      }
      ```

---

## 📌 Notes

* Les modèles et résultats sont stockés avec un **ID unique** (timestamp).
* Utiliser `"latest"` comme `model_id` pour charger automatiquement le dernier modèle sauvegardé.
* Les rapports et logs sont disponibles dans le dossier `reports/`.

---
