import os
import json
import requests
from importlib import import_module
from datetime import datetime

logger = import_module("07e_logger_config").logger

def envoyer_alerte_compliance(id_ordre, client_id, montant_chf, motif="Fat-Finger (> 100k CHF)", webhook_url=None):
    """
    Génère et envoie une alerte de conformité FINMA.
    Si aucun webhook_url n'est fourni, simule l'envoi et consigne dans le log.
    """
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    payload = {
        "event": "FINMA_COMPLIANCE_REJECT",
        "timestamp": horodatage,
        "severity": "CRITICAL",
        "details": {
            "ordre_id": id_ordre,
            "client_id": client_id,
            "montant_brut_chf": montant_chf,
            "motif_rejet": motif
        },
        "message": f"🚨 ALERTE COMPLIANCE : Rejet immédiat de l'ordre #{id_ordre} ({montant_chf:,.2f} CHF) pour le client {client_id}. Motif : {motif}."
    }

    # Logging immédiat dans l'audit trail
    logger.error(f"🚨 ALERTE DISPACHÉE : Ordre #{id_ordre} | Client {client_id} | Montant {montant_chf:,.2f} CHF | Motif: {motif}")

    # Envoi HTTP réel vers Webhook (MS Teams / Slack / PagerDuty) si l'URL est configurée
    webhook_target = webhook_url or os.getenv("WEBHOOK_ALERT_URL")
    if webhook_target:
        try:
            response = requests.post(webhook_target, json=payload, timeout=5)
            if response.status_code in [200, 201, 204]:
                logger.info("✅ Notification Webhook transmise avec succès à l'équipe Compliance.")
                return True
            else:
                logger.warning(f"⚠️ Échec d'envoi Webhook (Code HTTP {response.status_code}).")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la connexion au service de notification : {e}")
    else:
        logger.info("ℹ️ Mode Simulation Alerting : Aucun Webhook configuré, alerte enregistrée dans les logs.")

    return True

if __name__ == '__main__':
    # Test unitaire du module d'alerte
    envoyer_alerte_compliance(id_ordre=9901, client_id="C-8841", montant_chf=145000.00)