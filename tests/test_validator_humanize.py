
from unittest.mock import patch, MagicMock
import pytest

@pytest.fixture(autouse=True)
def mock_imports():
    """Mock missing dependencies to allow importing ValidationService."""
    with patch.dict('sys.modules', {
        'facturx': MagicMock(),
        'lxml': MagicMock(),
        'lxml.etree': MagicMock()
    }):
        yield

def test_humanize_errors_empty():
    """Test with an empty list of errors."""
    from app.services.validator import ValidationService
    assert ValidationService._humanize_errors([]) == []

def test_humanize_errors_none_or_empty_string():
    """Test that None or empty strings in the input are skipped."""
    from app.services.validator import ValidationService
    assert ValidationService._humanize_errors([None, "", "Unknown Error"]) == ["Unknown Error"]

def test_humanize_errors_unmapped():
    """Test that unmapped technical errors are returned as-is."""
    from app.services.validator import ValidationService
    tech_errors = ["Critical error: Flux capacitor depleted", "Random XML error"]
    assert ValidationService._humanize_errors(tech_errors) == tech_errors

def test_humanize_errors_mapping_date():
    """Test mapping for udt:DateTimeString."""
    from app.services.validator import ValidationService
    tech_errors = ["Value '202-01-01' is not a valid instance of udt:DateTimeString"]
    expected = ["Le format de la date est invalide (Format attendu: YYYYMMDD)."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mapping_context():
    """Test mapping for SpecifiedExchangedDocumentContext."""
    from app.services.validator import ValidationService
    tech_errors = ["Element 'SpecifiedExchangedDocumentContext' is missing"]
    expected = ["La structure du document est mal formée (Contexte manquant)."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mapping_id_unexpected():
    """Test mapping for ram:ID' is unexpected."""
    from app.services.validator import ValidationService
    tech_errors = ["Element 'ram:ID' is unexpected, expected is..."]
    expected = ["Le numéro de facture (ID) est mal positionné ou dupliqué."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mapping_seller_name():
    """Test mapping for Expected is ( {urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}Name )."""
    from app.services.validator import ValidationService
    tech_errors = ["Expected is ( {urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}Name )"]
    expected = ["Le nom de l'entreprise (Seller Name) est obligatoire."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mapping_postcode():
    """Test mapping for PostcodeCode."""
    from app.services.validator import ValidationService
    tech_errors = ["Element 'ram:PostcodeCode' is invalid"]
    expected = ["Le code postal est manquant dans l'adresse."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mapping_line_one():
    """Test mapping for LineOne."""
    from app.services.validator import ValidationService
    tech_errors = ["LineOne is mandatory"]
    expected = ["La première ligne de l'adresse est obligatoire."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mapping_country_id():
    """Test mapping for CountryID."""
    from app.services.validator import ValidationService
    tech_errors = ["CountryID must be present"]
    expected = ["Le code pays (ex: FR) est manquant."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mapping_currency_id():
    """Test mapping for currencyID."""
    from app.services.validator import ValidationService
    tech_errors = ["currencyID 'USD' is not allowed here"]
    expected = ["Le code devise (ex: EUR) est invalide ou absent."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mapping_type_code():
    """Test mapping for TypeCode."""
    from app.services.validator import ValidationService
    tech_errors = ["Missing TypeCode element"]
    expected = ["Le type de document (TypeCode 380) est manquant."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mapping_transaction():
    """Test mapping for SupplyChainTradeTransaction."""
    from app.services.validator import ValidationService
    tech_errors = ["SupplyChainTradeTransaction section is missing"]
    expected = ["La section Transaction (calculs) est manquante ou mal placée."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mapping_line_items():
    """Test mapping for IncludedSupplyChainTradeLineItem."""
    from app.services.validator import ValidationService
    tech_errors = ["IncludedSupplyChainTradeLineItem is required"]
    expected = ["Les lignes de facture (articles) sont obligatoires pour ce profil."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mapping_totals():
    """Test mapping for SpecifiedTradeSettlementHeaderMonetarySummation."""
    from app.services.validator import ValidationService
    tech_errors = ["SpecifiedTradeSettlementHeaderMonetarySummation is incomplete"]
    expected = ["La section Totaux est mal formée ou incomplète."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_deduplication_identical():
    """Test de-duplication of identical technical errors."""
    from app.services.validator import ValidationService
    tech_errors = ["CountryID", "CountryID"]
    expected = ["Le code pays (ex: FR) est manquant."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_deduplication_different_same_target():
    """Test de-duplication of different technical errors mapping to the same human message."""
    from app.services.validator import ValidationService
    tech_errors = ["CountryID is missing", "Invalid CountryID"]
    expected = ["Le code pays (ex: FR) est manquant."]
    assert ValidationService._humanize_errors(tech_errors) == expected

def test_humanize_errors_mixed():
    """Test a mix of mapped and unmapped errors with de-duplication."""
    from app.services.validator import ValidationService
    tech_errors = [
        "CountryID is missing",
        "Random error 1",
        "Invalid CountryID",
        "Random error 1",
        "TypeCode missing"
    ]
    expected = [
        "Le code pays (ex: FR) est manquant.",
        "Random error 1",
        "Le type de document (TypeCode 380) est manquant."
    ]
    assert ValidationService._humanize_errors(tech_errors) == expected
