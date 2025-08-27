# Question 02 : Pipeline de build et tests

Contraintes : 
- builds WebGL/Android/iOS < 20min
- taille limitée (50-80 Mo max)
- intégration Slack

___

## 1) Architecture CI/CD cible

**[Pipeline PR "rapide"]** : Pull Request -> Dev
- lint 
- tests (Edit/Play) 
- build smoke WebGL

**[Pipeline main "multi-plateformes"]** : Merge -> main
- Validate: cache warmup + tests + BVT (Build Verification Test) headless
- Build (en parallèle) pour vérifier que tout compile bien
- Metrics : Package + signature + métriques (taille, temps)
- Distrib + Slack : résumé, liens, artefacts, alertes, ...


## 2) Outils & réglages Unity (anti-conflits + vitesse)
**Versioning & assets**

-   **UnityYAMLMerge** (“Smart Merge”) pour `.unity`, `.prefab`, `.asset`.
    
-   **Git LFS + file locking** pour binaires (`.fbx`, `.wav`, `.mp4`, etc.).
    
-   Découpage **prefab variants** + **multi-scenes** pour réduire les conflits.
    
-   .gitignore strict (exclure `Library/`, `Temp/`, `Logs/`).
    

**Caches & perf de build**

-   **Unity Accelerator** commun (cible réseau faible latence).
    
-   Avoir un "runner" par config (Android, IOS, ...) avec **Editor/SDK pré-installé**.

    

# 3) Stratégie pipelines (3 types)

### A. Pipeline PR (≤ 12 min)

Objectif : retour rapide + éviter les merges qui cassent.

-   Lint C# (Roslyn/analyzers) + format (dotnet-format) + vérifs `.meta`.
    
-   **Tests EditMode** + **PlayMode ciblés** (scènes critiques) en headless.
    
-   **Smoke build WebGL** (démo/mini-scène) pour valider le pipeline.
    
-   **Slack**: statut + couverture + liens vers rapports.
    

### B. Pipeline main (≤ 20 min / plateforme)

Étapes parallélisées :

1.  **Validate**: warm cache, **BVT** (Build Verification Test) headless (charge menu, aucune exception, FPS minimal en PlayMode).
    
2.  **Build**:
    
    -   **WebGL (Linux)**: Brotli, _Enable Exceptions = None_, Data Caching, _Linker target_ minimal.
        
    -   **Android (Linux)**: dev=Mono rapide (internal), release=**IL2CPP** + R8 + **Play Asset Delivery** (base < 80 Mo, fast-follow/on-demand pour le reste).
        
    -   **iOS (macOS)**: Unity -> projet Xcode, puis `xcodebuild` archive + export IPA via **fastlane** (signing auto).
        
3.  **Quality Gates**: fail si taille > seuil, si tests < 95% OK, si logs contiennent exceptions.
    
4.  **Distrib**:
    
    -   WebGL -> **CDN** (avec headers Brotli/gzip + cache-busting).
        
    -   Android -> **Internal testing** (Play Console) / **Internal App Sharing**.
        
    -   iOS -> **TestFlight** (groupes QA).
        
5.  **Slack**: résumé (durées, tailles, changelog), liens artefacts, _promote_ buttons (slash-command).
    

### C. Pipeline release (tag `v*`)

-   Full tests + **IL2CPP** toutes plateformes, symboles + dSYMs, mapping R8.
    
-   Livraison **Beta** (puis **Production** via validation manuelle).
    
-   Génération changelog (Conventional Commits).
    

# 4) Stratégies de tests 

**Pyramide de tests Unity**

-   **Unitaires (EditMode)**: logique pure, DI (Zenject/NSubstitute).
    
-   **PlayMode**: comportements gameplay/UI, scènes clés, BVT démarrage.
    
-   **Intégration/E2E**:
    
    -   **Android/iOS**: **fastlane + Firebase Test Lab** (ou BrowserStack/App Center).
        
    -   **WebGL**: **Playwright** (smoke : page charge, WebGL context, télémetrie).
        
    -   **AltUnity Tester** (UI automation) ou **Airtest** pour flux critiques.
        
-   **Performance**: **Unity Performance Testing** (budgets FPS/mémoire), alerting si dérive.
    
-   **Visuel (snapshot)**: scènes de tests -> screenshots comparés (tolérance Δ).
    
-   **Crash & logs**: Sentry, Backtrace, Logstash, ...

**Qualité & gating**

-  Avoir une couverture min (p. ex. 60–70% logique critique).
    
-   BVT (Build Verification Test) obligatoire (avec un seuils taille/perf de reférence)
    

# 5) Optimisation taille (50–80 Mo)

Voici les points sensibles dans la gestion de la taille du build final

**Commun**

-   Addressables **on-demand**
    
-   Vérifier la compression et appliquer une compression spécifique selon l'env (ex: **ASTC/ETC2** pour Android).
    
-   Supprimer assets Editor-only, **Managed Stripping High**, **Strip Engine Code**.

-   Audio en sample rate réduit, mono si possible.
    
-   Désactiver symboles/Debug dans Player Settings de CI.
 

**Android**

-   **Play Asset Delivery**: base < 80 Mo (scènes initiales), le reste en **fast-follow**/**on-demand**.    


**WebGL**

-   Charger Addressables depuis CDN avec **cache-busting**.
    

# 6) Problèmes initiaux

Revenons sur les problèmes préalablement susse cités, et voyons comment notre implémentation les adresserais.

-   **Conflits assets** 
Force Text + meta visibles + UnityYAMLMerge + LFS locking + multi-scenes/prefab variants + politiques de branches (feature courte, PR rapide).
    
-   **Tests manuels uniquement**
Pyramide ci-dessus + device farm + BVT + visual/perf tests + gates.
    
-   **1/3 déploiements échouent** 
Versioning auto, validations taille/tests, _idempotent store uploads_, étapes atomiques + reprise, _release train_ cadencé.
    

# 7) Tenir les 20 minutes (pratiques clés)

-   **Cache serveur** + runners persistants (Library non supprimée entre jobs).
    
-   **Paralléliser** par plateforme; éviter jobs séquentiels.
    
-   **PR**: Android **Mono** + WebGL mini-scène (IL2CPP seulement sur release).
    
-   Meilleur Hardware (**Mac de qualité** pour iOS) 
    
-   **Limiter reimport** (Asset Database v2), éviter rebuild les Librairies au possible
    
-   **Adressables** -> base app plus petite, moins de compilation IL2CPP.
    
-   **Step “warmup”**: ouvrir une scène headless pour précompiler Burst.
    

# 8) Points d’attention Unity

-   **Déterminisme**: tests PlayMode flakys -> seeds fixes, Time.timeScale contrôlé.
    
-   **Plugins**: versions natives (AAR/Framework) alignées par plateforme.
    
-   **WebGL**: headers serveur (Brotli), CORS sur CDN, mémoire EMScripten.
    
-   **Signature**: gestion sûre des secrets CI (Keychain macOS, OIDC pour clouds).
    
-   **Numérotation builds**: unique et auto (date+SHA) -> évite échecs store.
    
-   **Observabilité**: métriques (temps build, taux échec, taille, test pass rate) exposées dans Slack/board.