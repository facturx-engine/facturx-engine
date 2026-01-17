# POLÍTICA DE SUPPORT - Factur-X API

## Support Officiel

### Versions Supportées

**Nous supportons UNIQUEMENT :**

- Version courante (N)
- Version précédente (N-1)

**Exemple :** Si la version actuelle est `1.5.0`, nous supportons `1.5.x` et `1.4.x` UNIQUEMENT.

### Si vous n'êtes PAS à jour

❌ **PAS DE SUPPORT**

Nous ne fournirons AUCUN support si vous utilisez :

- Une version plus ancienne que N-1
- Une version modifiée non officiellement
- Un environnement non documenté

### Procédure de Support

1. **Vérifiez votre version**

   ```
   curl http://localhost:8000/diagnostics | jq .version
   ```

2. **Mettez à jour si nécessaire**
   Voir `UPGRADE.md`

3. **Générez un support bundle**

   ```
   docker exec facturx-api python -m tools.support_bundle
   ```

4. **Envoyez le support bundle**
   - Email : <support@votre-domaine.com>
   - Avec le fichier `support_bundle.zip`
   - Et la description du problème

### Délais de Réponse

| Priorité | Délai | Conditions |
|----------|-------|------------|
| **Critique** | 4h | Production down, perte de données |
| **Haute** | 24h | Fonctionnalité majeure cassée |
| **Normale** | 72h | Bug non bloquant |
| **Basse** | Aucun SLA | Feature request, question |

**Critique/Haute** : Clients payants uniquement

### Exclusions de Support

Nous NE supportons PAS :

- ❌ Versions obsolètes (< N-1)
- ❌ Docker non officiel (images custom)
- ❌ Environnements modifiés
- ❌ Problèmes réseau/infrastructure
- ❌ Formation développeurs (voir documentation)
- ❌ Développement custom

### Auto-Support

Avant de contacter le support :

1. Consultez `/docs` (documentation API)
2. Vérifiez `RUNBOOK.md` (troubleshooting)
3. Consultez les logs : `docker logs facturx-api`
4. Testez avec `/diagnostics`

### Mise à Jour Obligatoire

Si une faille de sécurité est découverte :

- Patch publié sous 48h
- **Mise à jour OBLIGATOIRE sous 7 jours**
- Après 7 jours : AUCUN support pour versions non patchées

## TL;DR

✅ **Version N ou N-1** : Support complet
⚠️ **Version < N-1** : Mettez à jour d'abord
❌ **Version modifiée** : Pas de support

---

**Cette politique est NON NÉGOCIABLE**. Elle garantit la qualité du support en concentrant nos ressources sur les versions actuelles.
