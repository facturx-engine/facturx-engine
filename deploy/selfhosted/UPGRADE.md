# Factur-X API - Upgrade Guide

## Politique de Versions

Format : **vX.Y.Z** (SemVer)

- **X (Major)** : Breaking changes (incompatibilité API)
- **Y (Minor)** : Nouvelles fonctionnalités (rétrocompatible)
- **Z (Patch)** : Bug fixes uniquement

## Avant de commencer

1. **Vérifier la version actuelle**

   ```bash
   curl http://localhost:8000/diagnostics | jq .version
   ```

2. **Lire le CHANGELOG**
   Disponible sur le dépôt officiel

3. **Backup de la configuration**

   ```bash
   cp .env .env.backup
   cp docker-compose.yml docker-compose.yml.backup
   ```

## Procédure d'Upgrade

### Upgrade Minor/Patch (Simple - Zero Downtime)

Pour passer de `1.0.0` → `1.1.0` ou `1.0.1`

```bash
# 1. Pull la nouvelle image
docker pull facturx-api:1.1.0

# 2. Mettre à jour docker-compose.yml
sed -i 's/facturx-api:1.0.0/facturx-api:1.1.0/' docker-compose.yml

# 3. Redémarrer
docker-compose up -d

# 4. Vérifier
curl http://localhost:8000/diagnostics | jq .version
# Devrait afficher "1.1.0"
```

**Durée** : < 10 secondes de downtime

### Upgrade Major (Complexe - Peut nécessiter downtime)

Pour passer de `1.x.x` → `2.0.0`

```bash
# 1. Lire le guide de migration (fourni avec la release)
cat MIGRATION_v2.md

# 2. Tester en staging (si possible)

# 3. Planifier une fenêtre de maintenance

# 4. Arrêter le service
docker-compose down

# 5. Pull la nouvelle image
docker pull facturx-api:2.0.0

# 6. Mettre à jour docker-compose.yml
sed -i 's/facturx-api:1.x.x/facturx-api:2.0.0/' docker-compose.yml

# 7. Appliquer les changements de configuration (voir MIGRATION)

# 8. Démarrer
docker-compose up -d

# 9. Tester
curl http://localhost:8000/health
```

**Durée** : Variable (voir notes de release)

## Rollback

Si l'upgrade échoue :

```bash
# 1. Arrêter
docker-compose down

# 2. Restaurer la configuration
cp .env.backup .env
cp docker-compose.yml.backup docker-compose.yml

# 3. Redémarrer avec l'ancienne version
docker-compose up -d

# 4. Vérifier
curl http://localhost:8000/diagnostics | jq .version
```

## Checklist Post-Upgrade

- [ ] `/health` retourne `200 OK`
- [ ] `/diagnostics` retourne la nouvelle version
- [ ] Tester `/v1/convert` avec un PDF
- [ ] Tester `/v1/validate`
- [ ] Tester `/v1/extract`
- [ ] Vérifier les logs : `docker logs facturx-api`
- [ ] Vérifier la mémoire : `curl http://localhost:8000/diagnostics | jq .memory_status`

## Fréquence Recommandée

- **Patches** : Appliquer sous 1 semaine
- **Minor** : Appliquer sous 1 mois
- **Major** : Évaluer + planifier (pas d'urgence sauf sécurité)

## Notifications de Sécurité

En cas de faille de sécurité :

1. Notification par email
2. Patch publié sous 48h
3. **Application OBLIGATOIRE sous 7 jours**
4. Après 7 jours : support interrompu (voir SUPPORT_POLICY.md)

## Upgrade Path

Vous **DEVEZ** upgrader séquentiellement pour les versions majeures :

❌ **Interdit** : `1.0.0` → `3.0.0` (sauter des versions)
✅ **Correct** : `1.0.0` → `2.0.0` → `3.0.0`

Pour les minor/patch, vous pouvez sauter :
✅ **OK** : `1.0.0` → `1.5.2` (direct)

## Support Pendant l'Upgrade

Si problème :

1. Rollback immédiatement
2. Générer support bundle : `python -m tools.support_bundle`
3. Contacter support avec le bundle

---

**Toujours tester en staging avant la production !**
