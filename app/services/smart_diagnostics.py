"""
Smart Diagnostics Engine for Factur-X Validation Errors.

This module provides contextual, human-readable explanations for 
EN 16931 Schematron validation errors, going beyond raw technical codes.

Pro Feature: Transforms technical errors into actionable diagnostics.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from decimal import Decimal, InvalidOperation
import re
import logging
from lxml import etree

logger = logging.getLogger(__name__)


@dataclass
class Diagnostic:
    """A human-readable diagnostic for a validation error."""
    rule_id: str
    severity: str  # "error", "warning", "info"
    title: str  # Short, actionable title
    explanation: str  # Detailed explanation
    suggestion: str  # How to fix it
    context: Dict[str, Any] = field(default_factory=dict)  # Extracted values
    

@dataclass
class DiagnosticRule:
    """A rule that can analyze and enrich a raw validation error."""
    rule_id_pattern: str  # Regex pattern to match rule IDs
    analyzer: Callable[[Dict[str, Any], Optional[bytes]], Diagnostic]


class SmartDiagnosticsEngine:
    """
    Transforms raw Schematron errors into contextual, human-readable diagnostics.
    
    The engine uses a registry of DiagnosticRules, each specialized for a 
    specific error type (e.g., BR-CO-10 for VAT calculations).
    """
    
    # Technical tolerance for financial calculations (Chorus Pro allows up to 0.02)
    ROUNDING_TOLERANCE = Decimal("0.05")
    
    def __init__(self):
        self._rules: List[DiagnosticRule] = []
        self._register_builtin_rules()
    
    def _register_builtin_rules(self):
        """Register the Top 20 most common EN 16931 error rules."""
        
        # --- VAT Calculation Errors ---
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-CO-10",
            analyzer=self._analyze_vat_total_mismatch
        ))
        
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-CO-13",
            analyzer=self._analyze_line_total_mismatch
        ))
        
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-CO-14",
            analyzer=self._analyze_grand_total_mismatch
        ))
        
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-CO-15",
            analyzer=self._analyze_due_payable_mismatch
        ))
        
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-CO-16",
            analyzer=self._analyze_vat_category_sum
        ))
        
        # --- Missing Mandatory Fields ---
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-01",
            analyzer=self._analyze_missing_invoice_number
        ))
        
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-02",
            analyzer=self._analyze_missing_issue_date
        ))
        
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-04",
            analyzer=self._analyze_missing_seller_name
        ))
        
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-06",
            analyzer=self._analyze_missing_buyer_name
        ))
        
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-08",
            analyzer=self._analyze_missing_seller_address
        ))
        
        # --- Date Format Errors ---
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-03",
            analyzer=self._analyze_invalid_date_format
        ))
        
        # --- VAT Identifier Errors ---
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"BR-CO-09",
            analyzer=self._analyze_vat_identifier
        ))
        
        # --- Advanced Diagnostics (Angles Morts) ---
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"VAT-COUNTRY-MISMATCH",  # Custom trigger for cross-check
            analyzer=self._analyze_vat_country_mismatch
        ))
        
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"TYPE-AMOUNT-MISMATCH", 
            analyzer=self._analyze_invoice_type_vs_amount
        ))
        
        self._rules.append(DiagnosticRule(
            rule_id_pattern=r"INVALID-CHAR-IN-ID",
            analyzer=self._analyze_invoice_number_format
        ))
        
    def analyze(self, raw_errors: List[Dict[str, Any]], xml_content: Optional[bytes] = None) -> List[Diagnostic]:
        """
        Analyze a list of raw validation errors and return enriched diagnostics.
        """
        diagnostics = []
        
        # 1. Proactive Scan (Detect "Angles Morts" not caught by Schematron)
        if xml_content:
            diagnostics.extend(self._proactive_scan(xml_content))
        
        # 2. Enrich Schematron Errors
        for error in raw_errors:
            rule_id = error.get("rule_id", "")
            diagnostic = self._find_and_apply_rule(error, xml_content)
            
            if diagnostic:
                diagnostics.append(diagnostic)
            else:
                # Fallback: create a generic diagnostic
                diagnostics.append(Diagnostic(
                    rule_id=rule_id or "UNKNOWN",
                    severity=error.get("severity", "error"),
                    title=f"Validation Error: {rule_id}",
                    explanation=error.get("message", "A validation error occurred."),
                    suggestion="Review the invoice data and ensure it meets EN 16931 requirements."
                ))
        
        return diagnostics

    def _proactive_scan(self, xml_content: bytes) -> List[Diagnostic]:
        """Detect errors directly from XML (SIRET, Negative totals, etc.)."""
        diagnostics = []
        try:
            parser = etree.XMLParser(recover=True, no_network=True)
            root = etree.fromstring(xml_content, parser=parser)
            
            # Simple namespaces for CII
            ns = {
                'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
                'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100'
            }

            # 1. SIRET vs TVA Prefix
            vat_nodes = root.xpath('//ram:SellerTradeParty//ram:SpecifiedTaxRegistration/ram:ID[@schemeID="VA"]', namespaces=ns)
            country_nodes = root.xpath('//ram:SellerTradeParty//ram:PostalTradeAddress/ram:CountryID', namespaces=ns)
            if vat_nodes and country_nodes:
                vat_id = vat_nodes[0].text or ""
                country_code = country_nodes[0].text or ""
                if vat_id and country_code and not vat_id.startswith(country_code):
                    diagnostics.append(self._analyze_vat_country_mismatch({}, None))

            # 2. Negative Grand Total vs Type Code
            total_nodes = root.xpath('//ram:GrandTotalAmount', namespaces=ns)
            type_nodes = root.xpath('//rsm:ExchangedDocument/ram:TypeCode', namespaces=ns)
            if total_nodes and type_nodes:
                try:
                    total = Decimal(total_nodes[0].text or "0")
                    type_code = type_nodes[0].text or ""
                    if total < 0 and type_code == "380":
                        diagnostics.append(self._analyze_invoice_type_vs_amount({}, None))
                except (ValueError, InvalidOperation):
                    pass

            # 3. Forbidden Characters in Invoice ID
            id_nodes = root.xpath('//rsm:ExchangedDocument/ram:ID', namespaces=ns)
            if id_nodes:
                inv_id = id_nodes[0].text or ""
                if inv_id and not re.match(r'^[A-Za-z0-9/_-]+$', inv_id):
                    diagnostics.append(self._analyze_invoice_number_format({}, None))

        except Exception as e:
            logger.warning(f"Proactive scan failed: {e}")
            
        return diagnostics
    
    def _find_and_apply_rule(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Optional[Diagnostic]:
        """Find the matching rule and apply its analyzer."""
        rule_id = error.get("rule_id", "")
        
        for rule in self._rules:
            if re.match(rule.rule_id_pattern, rule_id):
                try:
                    return rule.analyzer(error, xml_content)
                except Exception as e:
                    logger.warning(f"Diagnostic rule {rule.rule_id_pattern} failed: {e}")
                    return None
        
        return None
    
    # =========================================================================
    # VAT Calculation Analyzers
    # =========================================================================
    
    def _get_cii_value(self, root: etree._Element, xpath: str) -> Decimal:
        """Helper to get Decimal value from CII XML."""
        ns = {'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100'}
        nodes = root.xpath(xpath, namespaces=ns)
        if nodes:
            try:
                return Decimal(nodes[0].text or "0")
            except (ValueError, InvalidOperation):
                pass
        return Decimal("0")

    def _analyze_vat_total_mismatch(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-CO-10: Sum of line VAT amounts != Invoice VAT total."""
        explanation = "The sum of line VAT amounts does not match the declared total VAT."
        
        if xml_content:
            try:
                root = etree.fromstring(xml_content)
                declared = self._get_cii_value(root, '//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxTotalAmount')
                explanation += f" (Declared Total: {declared}€)."
            except (etree.XMLSyntaxError, ValueError):
                pass

        return Diagnostic(
            rule_id="BR-CO-10",
            severity="error",
            title="VAT Total Calculation Error",
            explanation=explanation,
            suggestion=(
                f"Verify your rounding. A technical tolerance of {self.ROUNDING_TOLERANCE}€ is applied. "
                "Ensure that the sum of (Basis * Rate) for each line equals the total VAT exactly."
            )
        )
    
    def _analyze_line_total_mismatch(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-CO-13: Sum of line net amounts != Invoice line total."""
        return Diagnostic(
            rule_id="BR-CO-13",
            severity="error",
            title="Écart sur le Total HT des Lignes",
            explanation="Le total net (HT) de la facture ne correspond pas à la somme des montants HT des lignes.",
            suggestion=(
                "Recalculez : somme(quantité * prix_net). "
                "Si l'écart est < 0.05€, vérifiez si vous devez utiliser le champ BT-114 (Arrondi)."
            )
        )
    
    def _analyze_grand_total_mismatch(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-CO-14: tax_basis_total + tax_total != grand_total."""
        delta_info = ""
        if xml_content:
            try:
                root = etree.fromstring(xml_content)
                ht = self._get_cii_value(root, '//ram:TaxBasisTotalAmount')
                tva = self._get_cii_value(root, '//ram:TaxTotalAmount')
                ttc = self._get_cii_value(root, '//ram:GrandTotalAmount')
                delta = abs((ht + tva) - ttc)
                if delta <= self.ROUNDING_TOLERANCE:
                    return Diagnostic(
                        rule_id="BR-CO-14",
                        severity="warning",
                        title="Rounding Warning (Grand Total)",
                        explanation=f"Rounding difference detected: {delta}€. This is acceptable but could be optimized.",
                        suggestion="Add a rounding line (BT-114) to balance exactly: Net + VAT = Grand Total."
                    )
                delta_info = f" (Difference: {delta}€)."
            except (etree.XMLSyntaxError, ValueError):
                pass

        return Diagnostic(
            rule_id="BR-CO-14",
            severity="error",
            title="Grand Total Error",
            explanation=f"The declared Grand Total does not match the sum of Net Amount + VAT{delta_info}.",
            suggestion="Verify the equation: Total Net + Total VAT = Grand Total."
        )
    
    def _analyze_due_payable_mismatch(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-CO-15: due_payable != grand_total - prepaid."""
        return Diagnostic(
            rule_id="BR-CO-15",
            severity="error",
            title="Amount Due Calculation Error",
            explanation=(
                "The amount due for payment should equal the grand total minus any prepaid amounts."
            ),
            suggestion=(
                "Verify: due_payable = grand_total - prepaid\n"
                "If there is no prepayment, due_payable should equal grand_total."
            )
        )
    
    def _analyze_vat_category_sum(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-CO-16: VAT category amounts must sum to tax_total."""
        return Diagnostic(
            rule_id="BR-CO-16",
            severity="error",
            title="VAT Breakdown Calculation Error",
            explanation=(
                "The sum of all VAT amounts from the tax_details breakdown does not match "
                "the declared tax_total."
            ),
            suggestion=(
                "1. Verify each entry in 'tax_details'\n"
                "2. Ensure calculated_amount = basis_amount × (rate / 100)\n"
                "3. Sum all calculated_amounts and update tax_total"
            )
        )
    
    # =========================================================================
    # Missing Field Analyzers
    # =========================================================================
    
    def _analyze_missing_invoice_number(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-01: Invoice number is mandatory."""
        return Diagnostic(
            rule_id="BR-01",
            severity="error",
            title="Missing Invoice Number",
            explanation="An invoice must have a unique identifier (invoice number).",
            suggestion="Add 'invoice_number' to your JSON payload."
        )
    
    def _analyze_missing_issue_date(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-02: Issue date is mandatory."""
        return Diagnostic(
            rule_id="BR-02",
            severity="error",
            title="Missing Issue Date",
            explanation="An invoice must have an issue date.",
            suggestion="Add 'issue_date' in YYYYMMDD format (e.g., '20260208')."
        )
    
    def _analyze_missing_seller_name(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-04: Seller name is mandatory."""
        return Diagnostic(
            rule_id="BR-04",
            severity="error",
            title="Missing Seller Name",
            explanation="The seller (vendor) must have a legal name.",
            suggestion="Add 'name' to the 'seller' object in your payload."
        )
    
    def _analyze_missing_buyer_name(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-06: Buyer name is mandatory."""
        return Diagnostic(
            rule_id="BR-06",
            severity="error",
            title="Missing Buyer Name",
            explanation="The buyer (customer) must have a legal name.",
            suggestion="Add 'name' to the 'buyer' object in your payload."
        )
    
    def _analyze_missing_seller_address(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-08: Seller postal address is mandatory at EN16931 profile."""
        return Diagnostic(
            rule_id="BR-08",
            severity="error",
            title="Missing Seller Address",
            explanation=(
                "For the EN16931 profile, the seller must have a complete postal address "
                "including at minimum: country_code."
            ),
            suggestion="Add 'address' with at least 'country_code' to the 'seller' object."
        )
    
    # =========================================================================
    # Date Format Analyzers
    # =========================================================================
    
    def _analyze_invalid_date_format(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-03: Date format must be YYYYMMDD."""
        return Diagnostic(
            rule_id="BR-03",
            severity="error",
            title="Invalid Date Format",
            explanation=(
                "Dates in Factur-X must be in YYYYMMDD format without separators. "
                "For example: '20260208' for February 8th, 2026."
            ),
            suggestion=(
                "Convert dates to YYYYMMDD format:\n"
                "- issue_date: '20260208'\n"
                "- due_date: '20260308'\n"
                "Do not use dashes, slashes, or other separators."
            )
        )
    
    # =========================================================================
    # VAT Identifier Analyzers
    # =========================================================================
    
    def _analyze_vat_identifier(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """BR-CO-09: VAT identifier format."""
        return Diagnostic(
            rule_id="BR-CO-09",
            severity="error",
            title="Invalid VAT Identifier",
            explanation=(
                "A VAT identifier must start with a valid 2-letter country code (ISO 3166-1 alpha-2) "
                "followed by the national VAT number."
            ),
            suggestion=(
                "Ensure vat_number follows the format: 'XX123456789'\n"
                "Examples:\n"
                "- France: 'FR12345678901'\n"
                "- Germany: 'DE123456789'\n"
                "- Belgium: 'BE0123456789'"
            )
        )

    # =========================================================================
    # Advanced Diagnostics (Angles Morts)
    # =========================================================================

    def _analyze_vat_country_mismatch(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """Check SIRET/VAT prefix vs Country Code."""
        return Diagnostic(
            rule_id="BR-CO-09-EXT",
            severity="error",
            title="Incohérence Pays / TVA",
            explanation=(
                "Le numéro de TVA intracommunautaire doit commencer par le code pays "
                "spécifié dans l'adresse du vendeur."
            ),
            suggestion=(
                "Vérifiez que le préfixe de 'vat_number' (ex: FR) correspond au 'country_code' "
                "du vendeur (BT-40)."
            )
        )

    def _analyze_invoice_type_vs_amount(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """Suggest code 381 for negative totals."""
        return Diagnostic(
            rule_id="BT-3-CONTEXT",
            severity="error",
            title="Type de Facture Incorrect (Avoir)",
            explanation=(
                "Un montant total négatif indique généralement un Avoir, qui nécessite "
                "le code type '381' (Credit Note) au lieu de '380'."
            ),
            suggestion="Changez le 'type_code' en '381' pour les montants négatifs."
        )

    def _analyze_invoice_number_format(self, error: Dict[str, Any], xml_content: Optional[bytes]) -> Diagnostic:
        """Check for forbidden characters in BT-1."""
        return Diagnostic(
            rule_id="BT-1-FORMAT",
            severity="error",
            title="Caractères Interdits dans le Numéro",
            explanation=(
                "Certains caractères spéciaux (@, #, <, >, &, etc.) provoquent des rejets "
                "systématiques sur les plateformes comme Chorus Pro."
            ),
            suggestion=(
                "Utilisez uniquement des caractères alphanumériques et les séparateurs "
                "autorisés : tiret (-), underscore (_) et slash (/)."
            )
        )


# Singleton instance for easy access
_engine: Optional[SmartDiagnosticsEngine] = None


def get_diagnostics_engine() -> SmartDiagnosticsEngine:
    """Get the singleton SmartDiagnosticsEngine instance."""
    global _engine
    if _engine is None:
        _engine = SmartDiagnosticsEngine()
    return _engine
