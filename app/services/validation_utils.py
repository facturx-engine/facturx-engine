import logging
from typing import List, Tuple, Optional
from lxml import etree
from facturx import get_flavor, get_level

logger = logging.getLogger(__name__)

# Dictionary mapping technical XSD substrings to user-friendly messages
ERROR_MAP = {
    "udt:DateTimeString": "Le format de la date est invalide (Format attendu: YYYYMMDD).",
    "SpecifiedExchangedDocumentContext": "La structure du document est mal formée (Contexte manquant).",
    "ram:ID' is unexpected": "Le numéro de facture (ID) est mal positionné ou dupliqué.",
    "Expected is ( {urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}Name )": "Le nom de l'entreprise (Seller Name) est obligatoire.",
    "PostcodeCode": "Le code postal est manquant dans l'adresse.",
    "LineOne": "La première ligne de l'adresse est obligatoire.",
    "CountryID": "Le code pays (ex: FR) est manquant.",
    "currencyID": "Le code devise (ex: EUR) est invalide ou absent.",
    "TypeCode": "Le type de document (TypeCode 380) est manquant.",
    "SupplyChainTradeTransaction": "La section Transaction (calculs) est manquante ou mal placée.",
    "IncludedSupplyChainTradeLineItem": "Les lignes de facture (articles) sont obligatoires pour ce profil.",
    "SpecifiedTradeSettlementHeaderMonetarySummation": "La section Totaux est mal formée ou incomplète.",
}

def humanize_errors(technical_errors: List[str]) -> List[str]:
    """Converts cryptic technical errors into human-readable guidance."""
    human_errors = []
    if not technical_errors:
        return []
        
    for err in technical_errors:
        if not err:
            continue
        err_str = str(err)
        found = False
        for tech_pattern, human_msg in ERROR_MAP.items():
            if tech_pattern in err_str:
                human_errors.append(human_msg)
                found = True
                break
        if not found:
            # Fallback to original if no mapping found
            human_errors.append(err_str)
    return list(dict.fromkeys(human_errors)) # Remove duplicates

def detect_format(xml_etree: etree._Element) -> Tuple[Optional[str], Optional[str]]:
    """
    Detects the format (flavor) and profile (level) of a Factur-X/ZUGFeRD/XRechnung XML.
    
    Returns:
        Tuple[format, profile] e.g. ("factur-x", "en16931")
    """
    try:
        # 1. Check for UBL (XRechnung)
        # UBL uses 'Invoice' as root but acts different from CII
        if 'urn:oasis:names:specification:ubl' in xml_etree.tag or \
           any('urn:oasis:names:specification:ubl' in str(ns) for ns in (xml_etree.nsmap.values() if xml_etree.nsmap else [])):
            return "ubl", "xrechnung"

        # 2. Check for Factur-X / ZUGFeRD (CII)
        detected_format = get_flavor(xml_etree)
        detected_flavor = get_level(xml_etree)
        return detected_format, detected_flavor
    except Exception as e:
        # Resilience: Handle newer URNs (like XRechnung 3.0) not yet in facturx library
        urn_xpath = "//*[local-name()='GuidelineSpecifiedDocumentContextParameter']/*[local-name()='ID']"
        urn_el = xml_etree.xpath(urn_xpath)
        urn = urn_el[0].text if (urn_el and urn_el[0].text) else ""
        
        if "en16931" in urn.lower() or "xrechnung" in urn.lower():
            logger.info(f"Using fallback flavor detection for URN: {urn}")
            return "factur-x", "en16931" # Map to CII behavior
        else:
            raise e
