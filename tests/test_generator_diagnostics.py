from app.services.generator import GeneratorService


def test_blocking_diagnostics_are_reported_before_warnings():
    diagnostics = [
        {
            "rule_id": "PEPPOL-EN16931-R008",
            "message": "Document MUST not contain empty elements.",
            "severity": "warning",
        },
        {
            "rule_id": "BR-FR-CO-05",
            "message": "A credit note must reference the preceding invoice.",
            "severity": "fatal",
        },
    ]

    message = GeneratorService._format_validation_errors(diagnostics)

    assert message.startswith("[BR-FR-CO-05]")
    assert "PEPPOL-EN16931-R008" not in message
