import unittest
from unittest.mock import patch, MagicMock
from app.services.smart_diagnostics import SmartDiagnosticsEngine

class TestSmartDiagnosticsSecurity(unittest.TestCase):
    def setUp(self):
        self.engine = SmartDiagnosticsEngine()

    def _setup_mock_root(self, mock_fromstring):
        mock_root = MagicMock()
        mock_node = MagicMock()
        mock_node.text = "10.00"
        mock_root.xpath.return_value = [mock_node]
        mock_fromstring.return_value = mock_root
        return mock_root

    @patch('app.services.smart_diagnostics.etree.fromstring')
    def test_analyze_vat_total_mismatch_uses_secure_parser(self, mock_fromstring):
        # Setup
        self._setup_mock_root(mock_fromstring)
        xml_content = b"<root></root>"

        # Execute
        self.engine._analyze_vat_total_mismatch({}, xml_content)

        # Verify
        args, kwargs = mock_fromstring.call_args
        self.assertIn('parser', kwargs, "Parser argument missing in _analyze_vat_total_mismatch")
        parser = kwargs['parser']
        # Verify it is the secure parser instance
        self.assertIs(parser, SmartDiagnosticsEngine._SECURE_PARSER)


    @patch('app.services.smart_diagnostics.etree.fromstring')
    def test_analyze_grand_total_mismatch_uses_secure_parser(self, mock_fromstring):
        # Setup
        self._setup_mock_root(mock_fromstring)
        xml_content = b"<root></root>"

        # Execute
        self.engine._analyze_grand_total_mismatch({}, xml_content)

        # Verify
        args, kwargs = mock_fromstring.call_args
        self.assertIn('parser', kwargs, "Parser argument missing in _analyze_grand_total_mismatch")
        parser = kwargs['parser']
        self.assertIs(parser, SmartDiagnosticsEngine._SECURE_PARSER)

    @patch('app.services.smart_diagnostics.etree.fromstring')
    def test_proactive_scan_uses_secure_parser(self, mock_fromstring):
        # Setup
        self._setup_mock_root(mock_fromstring)
        xml_content = b"<root></root>"

        # Execute
        self.engine._proactive_scan(xml_content)

        # Verify
        args, kwargs = mock_fromstring.call_args
        self.assertIn('parser', kwargs, "Parser argument missing in _proactive_scan")
        parser = kwargs['parser']
        self.assertIs(parser, SmartDiagnosticsEngine._SECURE_PARSER)

if __name__ == '__main__':
    unittest.main()
