import unittest
from .generate_levels import back_propagate, _solved

class BackPropagateTests(unittest.TestCase):
    def test_example_move(self):
        bases = [["a", "a"], ["b", "b"], []]
        heights = [2, 2, 2]
        states = back_propagate(bases, heights)
        expected = [
            [["a"], ["b", "b"], ["a"]],
            [["a", "a"], ["b"], ["b"]],
        ]
        self.assertEqual({tuple(tuple(b) for b in s) for s in states},
                         {tuple(tuple(b) for b in s) for s in expected})
        for s in states:
            self.assertFalse(_solved(s, heights))

    def test_three_high_bases(self):
        bases = [["a", "a", "a"], ["b", "b", "b"], []]
        heights = [3, 3, 3]
        states = back_propagate(bases, heights)
        expected = [
            [["a", "a"], ["b", "b", "b"], ["a"]],
            [["a"], ["b", "b", "b"], ["a", "a"]],
            [["a", "a", "a"], ["b", "b"], ["b"]],
            [["a", "a", "a"], ["b"], ["b", "b"]],
        ]
        self.assertEqual({tuple(tuple(b) for b in s) for s in states},
                         {tuple(tuple(b) for b in s) for s in expected})

    def test_error_on_unsolved_input(self):
        bases = [["a"], ["a"], []]
        heights = [2, 2, 2]
        with self.assertRaises(ValueError):
            back_propagate(bases, heights)

if __name__ == '__main__':
    unittest.main()
