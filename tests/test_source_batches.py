# ruff: noqa: E701, E702, E401, F401, E731, B905, I001
import unittest
import torch
from ronin.data.source_batches import SourceBalancedBatches

class SourceBalancedBatchTests(unittest.TestCase):
    def make(self, seed):
        sources=[("a",torch.arange(4096,dtype=torch.long),0.5),("b",torch.arange(5000,dtype=torch.long),0.495),("c",torch.arange(6000,dtype=torch.long),0.005)]
        return SourceBalancedBatches(sources,batch_size=4,sequence_length=32,seed=seed)

    def test_reproducible_batches(self):
        left=iter(self.make(2026)); right=iter(self.make(2026))
        for _ in range(3):
            lx,ly=next(left); rx,ry=next(right)
            self.assertTrue(torch.equal(lx,rx)); self.assertTrue(torch.equal(ly,ry))
            self.assertEqual(tuple(lx.shape),(4,32)); self.assertEqual(tuple(ly.shape),(4,32))

    def test_probabilities_are_normalized_and_reported(self):
        sampler=self.make(17)
        report=sampler.sampling_report()
        self.assertAlmostEqual(sum(item["target_probability"] for item in report["sources"]),1.0)
        iterator=iter(sampler)
        for _ in range(25): next(iterator)
        report=sampler.sampling_report()
        self.assertEqual(report["total_windows"],100)
        self.assertLessEqual(report["sources"][2]["observed_probability"],0.05)

    def test_rejects_short_source(self):
        with self.assertRaises(ValueError):
            SourceBalancedBatches([("short",torch.arange(8),1.0)],2,8)

if __name__=="__main__": unittest.main()
