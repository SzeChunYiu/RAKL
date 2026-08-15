import unittest
from recursive_framework_audit_reference import *

class TestReference(unittest.TestCase):
    def test_wrong_question(self):
        self.assertEqual(decide(Node(),Residual((Coordinate.QUESTION,))).action,Action.REFRAME_QUESTION)
    def test_wrong_framework(self):
        self.assertEqual(decide(Node(),Residual((Coordinate.FRAMEWORK,))).action,Action.CHALLENGE_FRAMEWORK)
    def test_false_merge(self):
        self.assertEqual(decide(Node(),Residual(split_required=True)).action,Action.SPLIT)
    def test_false_split(self):
        self.assertEqual(decide(Node(),Residual(merge_required=True)).action,Action.MERGE)
    def test_interface(self):
        self.assertEqual(decide(Node(),Residual((Coordinate.INTERFACE,))).action,Action.REPAIR_INTERFACE)
    def test_measurement(self):
        self.assertEqual(decide(Node(),Residual((Coordinate.MEASUREMENT,))).action,Action.REVISE_MEASUREMENT)
    def test_evaluator(self):
        self.assertEqual(decide(Node(),Residual(evaluator_invalid=True)).action,Action.AUDIT_EVALUATOR)
    def test_ambiguous(self):
        self.assertEqual(decide(Node(),Residual((Coordinate.FRAMEWORK,Coordinate.MEASUREMENT))).action,Action.RUN_DISCRIMINATOR)
    def test_ascend(self):
        r=Residual((Coordinate.ATOM,),parent_challenge_supported=True,distinct_local_repair_families_failed=2)
        self.assertEqual(decide(Node(),r).action,Action.ASCEND)
    def test_external(self):
        self.assertEqual(decide(Node(),Residual(external_trust_root=True)).action,Action.EXTERNAL_TRUST_ROOT)
    def test_resource(self):
        self.assertEqual(decide(Node(),Residual(resource_bound=True)).action,Action.CANNOT_CHECK)
    def test_stop(self):
        self.assertEqual(decide(Node(True,False),Residual()).action,Action.STOP_BOUNDED)
    def test_default(self):
        self.assertEqual(decide(Node(False,False),Residual()).action,Action.SOLVE_CURRENT)
    def test_nonsovereign(self):
        d=decide(Node(),Residual((Coordinate.QUESTION,)))
        self.assertFalse(d.grants_scientific_authority)
        self.assertFalse(d.grants_method_promotion_authority)

if __name__=="__main__":
    unittest.main()
