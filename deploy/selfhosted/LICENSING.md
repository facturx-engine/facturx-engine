# Factur-X API - Licensing

## License Tiers

### Community Edition (Gratuite)

**Fonctionnalités incluses:**

- ✅ `/v1/convert` - Conversion PDF → Factur-X
- ✅ `/v1/validate` - Validation EN 16931
- ✅ `/v1/extract` - Extraction et parsing JSON
- ✅ Documentation complète (`/docs`)
- ✅ Support community (GitHub Issues)
- ✅ Mises à jour de sécurité

**Limitations:**

- Aucune limite technique
- Support community uniquement (pas de SLA)
- Pas de support commercial

**Activation:**

```bash
# Dans .env
# Ne PAS définir LICENSE_KEY
```

### Paid Edition

**Fonctionnalités additionnelles:**

- ✅ Support commercial avec SLA
- ✅ Accès priority aux bugfixes
- ✅ Fonctionnalités futures premium
- ✅ Consultation architecture

**Prix:** Nous contacter

**Activation:**

```bash
# Dans .env
LICENSE_KEY=votre-cle-de-licence
```

## Detection de la Licence

L'API détecte automatiquement le mode :

```bash
curl http://localhost:8000/diagnostics | jq .features_enabled
```

**Réponse Community :**

```json
{
  "features_enabled": ["validate", "convert", "extract", "mode:community"]
}
```

**Réponse Paid :**

```json
{
  "features_enabled": ["validate", "convert", "extract", "mode:paid"]
}
```

## Air-Gapped Licensing

Pour les environnements sans Internet :

### Activation par Variable d'Environnement (Standard)

Pour tous les environnements (Docker, Kubernetes, Air-Gapped) :

```bash
# Dans .env ou var d'env
LICENSE_KEY=votre-cle-de-licence-base64
```

## Vérification de Licence

La licence est vérifiée au démarrage uniquement. Aucun "phone home" pendant l'exécution.

### Informations Collectées

**Mode Community :** RIEN. Zéro télémétrie.

**Mode Paid :** RIEN non plus, sauf si vous activez explicitement les rapports d'erreurs optionnels.

## Conformité

- **RGPD** : Aucune donnée personnelle collectée
- **Privacy** : Les PDFs/factures ne sont JAMAIS loggés ou transmis
- **Open Source** : Functional Source License (FSL) 1.1

## FAQ

**Q: Que se passe-t-il si ma licence expire?**
R: Le système repasse automatiquement en mode Community. Aucune interruption de service.

**Q: Puis-je utiliser la version Community en production?**
R: Oui, aucune restriction.

**Q: La licence est-elle liée à un nombre d'utilisateurs/requêtes?**
R: Non. License par instance/serveur uniquement.

**Q: Comment upgrader vers la version Paid?**
R: Contactez-nous → Recevez la clé → Ajoutez à `.env` → Redémarrez. < 5 minutes.

## Contact Commercial

- Achat & Clés : [Factur-X Engine sur Lemon Squeezy](https://facturx-engine.lemonsqueezy.com)

---

**TL;DR:** Community = gratuit illimité. Paid = support professionnel.
