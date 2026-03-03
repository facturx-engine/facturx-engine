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
    # XRechnung / EN16931 Specific Mappings (Audit Fixes)
    "BR-DE-11": "Le montant total de la facture doit être égal à la somme des montants HT et de la TVA.",
    "BR-DE-1": "Le numéro de facture (BT-1) est obligatoire.",
    "BR-DE-2": "La date d'émission de la facture (BT-2) est obligatoire.",
    "BR-DE-4": "La référence de l'acheteur (BT-10) est obligatoire pour l'XRechnung.",
    "XSD-INVALID": "Erreur de structure XML: Le fichier ne respecte pas le schéma technique officiel.",
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
        # 1. Identify URN / Guideline ID
        # CII path: GuidelineSpecifiedDocumentContextParameter/ID
        # UBL path: CustomizationID (or cbc:CustomizationID)
        urn = ""
        nsmap = xml_etree.nsmap
        
        # Try CII extraction
        urn_xpath = "//*[local-name()='GuidelineSpecifiedDocumentContextParameter']/*[local-name()='ID']"
        urn_el = xml_etree.xpath(urn_xpath)
        if urn_el and urn_el[0].text:
            urn = urn_el[0].text
        
        # Try UBL extraction if empty
        if not urn:
            ubl_xpath = "/*[local-name()='Invoice']/*[local-name()='CustomizationID']"
            ubl_el = xml_etree.xpath(ubl_xpath)
            if ubl_el and ubl_el[0].text:
                urn = ubl_el[0].text

        # 2. Check for UBL (XRechnung / Peppol)
        is_ubl = 'urn:oasis:names:specification:ubl' in xml_etree.tag or \
                 any('urn:oasis:names:specification:ubl' in str(ns) for ns in (nsmap.values() if nsmap else []))

        if is_ubl:
            profile = "en16931"
            if "xrechnung" in urn.lower():
                # Extract version from URN like urn:xeinkauf.de:kosit:xrechnung_3.0
                if "3.0" in urn:
                    profile = "xrechnung_3.0"
                elif "2.3" in urn:
                    profile = "xrechnung_2.3"
            return "ubl", profile

        # 3. Check for Factur-X / ZUGFeRD / XRechnung (CII)
        if "xrechnung" in urn.lower():
            if "3.0" in urn:
                return "factur-x", "xrechnung_3.0"
            if "2.3" in urn:
                return "factur-x", "xrechnung_2.3"

        # 4. Manual mapping for standard Factur-X / ZUGFeRD profiles 
        # (Avoids facturx library crashes on some ZUGFeRD 2.0 files with empty namespace prefixes)
        urn_lower = urn.lower()
        if "urn:cen.eu:en16931:2017" in urn_lower or "urn:factur-x.eu:1p0" in urn_lower:
            if "basicwl" in urn_lower or "basic-wl" in urn_lower:
                return "factur-x", "basicwl"
            if "basic" in urn_lower:
                return "factur-x", "basic"
            if "minimum" in urn_lower:
                return "factur-x", "minimum"
            if "extended" in urn_lower:
                return "factur-x", "extended"
            # Default to en16931 if it matches the CEN URN
            if "urn:cen.eu:en16931:2017" in urn_lower:
                return "factur-x", "en16931"

        # Fallback to facturx library for other cases
        detected_format = get_flavor(xml_etree)
        detected_flavor = get_level(xml_etree)
        return detected_format, detected_flavor

    except Exception as e:
        logger.warning(f"Detection error, attempting heuristic fallback: {e}")
        # Final fallback: if it looks like XRechnung, at least tag it for CII processing
        xml_head = str(etree.tostring(xml_etree, encoding='unicode', method='xml')[:500]).lower()
        if "xrechnung" in xml_head:
            return "factur-x", "en16931"
        raise e
