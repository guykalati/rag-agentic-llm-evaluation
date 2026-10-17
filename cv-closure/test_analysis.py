import unittest
from analyze_results import anchor_coverage,citation_ids
class RetrievalDiagnosticChecks(unittest.TestCase):
    def test_source_and_phrase_are_both_required(self):
        source={'source_url':'a','anchor_phrase':'kill the child'}
        self.assertEqual(anchor_coverage([source],[{'source_url':'b','text':'kill the child'}]),[False])
        self.assertEqual(anchor_coverage([source],[{'source_url':'a','text':'KILL  THE child'}]),[True])
    def test_quoted_code_or_prose_ids_are_not_citations(self):
        self.assertEqual(citation_ids('Prose json:000001 and [json:000002, pathlib:006160].'),['json:000002','pathlib:006160'])
