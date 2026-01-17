# Factur-X API - Operations Runbook

## Installation

### Docker (Recommandé)

```bash
# 1. Cloner / copier les fichiers
cd /opt/facturx-api
cp . env.example .env

# 2. Build l'image
docker build -t facturx-api:1.0.0 ../..

# 3. Démarrer
docker-compose up -d

# 4. Vérifier
curl http://localhost:8000/health
```

### Manuel (Dev uniquement)

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Maintenance

### Logs

```bash
# Voir les logs
docker logs facturx-api -f

# Logs des 100 dernières lignes
docker logs facturx-api --tail 100
```

### Redémarrer

```bash
docker-compose restart facturx-api
```

### Arrêter

```bash
docker-compose down
```

## Troubleshooting

### Le service ne démarre pas

**Symptôme** : `docker-compose up` échoue

**Solutions** :

1. Vérifier les ports :

   ```
   netstat -an | findstr :8000
   ```

2. Vérifier la mémoire :

   ```
   docker stats
   ```

3. Vérifier les logs :

   ```
   docker logs factur-api
   ```

### API retourne 500

**Symptôme** : Toutes les requêtes retournent 500

**Solutions** :

1. Vérifier `/diagnostics` :

   ```
   curl http://localhost:8000/diagnostics
   ```

2. Vérifier la mémoire disponible
3. Redémarrer le service

### Conversion échoue

**Symptôme** : `/v1/convert` retourne 400

**Solutions** :

1. Vérifier la taille du PDF (< 10MB par défaut)
2. Vérifier le format du JSON metadata
3. Tester avec `/docs` (Swagger)

### Validation échoue

**Symptôme** : `/v1/validate` retourne `valid: false`

**Solutions** :

1. Le PDF doit contenir du XML Factur-X
2. Vérifier le profil détecté dans la réponse
3. Tester d'abord avec `/v1/extract` pour voir le contenu

## Diagnostics

### Health Check

```bash
curl http://localhost:8000/health
# Devrait retourner: {"status":"healthy"}
```

### Diagnostics Complets

```bash
curl http://localhost:8000/diagnostics | jq
```

Vérifier :

- `version` : Version de l'API
- `features_enabled` : Fonctionnalités actives
- `memory_status` : État de la mémoire

### Support Bundle

```bash
docker exec facturx-api python -m tools.support_bundle
docker cp facturx-api:/app/support_bundle.zip .
```

## Performance

### Limites Recommandées

- **RAM** : 512MB minimum, 1GB recommandé
- **CPU** : 1 core minimum, 2+ recommandé
- **Disk** : 1GB pour l'application + logs
- **Upload** : 10MB par défaut (configurable via `MAX_UPLOAD_SIZE_MB`)

### Scaling

Pour augmenter le nombre de workers :

```bash
# Dans .env
WORKERS=8
docker-compose restart
```

## Sécurité

### Air-Gapped

Le système fonctionne 100% offline. Aucun accès Internet requis.

### Données

- Les PDFs ne sont JAMAIS loggés
- Les métadonnées ne sont JAMAIS persistées
- Stateless : aucune donnée stockée entre requêtes

## Backup

Aucun backup nécessaire : l'API est 100% stateless.

Backupez uniquement :

- `.env` (configuration)
- `docker-compose.yml` (si modifié)

## Updates

Voir `UPGRADE.md` pour la procédure complète.
