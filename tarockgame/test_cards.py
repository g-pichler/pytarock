import unittest
from cards import Card, CardCollection, Suit


class CardTest(unittest.TestCase):
    def test_cardcollection(self):
        c = list()
        c.append(Card(suit=Suit.DIAMONDS,
                       value=1))
        c.append(Card(suit=Suit.CLUBS,
                        value=6))
        c.append(Card(suit=Suit.TAROCK,
                      value=21))

        cc = CardCollection([c[0]])

        self.assertTrue(c[0] in cc)
        self.assertFalse(c[1] in cc)
        self.assertFalse(c[2] in cc)

        cc.add(c[1])
        cc.add(c[2])

        self.assertTrue(c[2] in cc)

        for i, c0 in enumerate(cc):
            self.assertEqual(c[i], c0)


if __name__ == '__main__':
    unittest.main()
