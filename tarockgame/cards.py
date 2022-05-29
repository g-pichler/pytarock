#!/usr/bin/env python
# *-* encoding: utf-8 *-*


from enum import Enum
from typing import Set, Iterable, List


class Suit(Enum):
    HEARTS = 1
    CLUBS = 2
    DIAMONDS = 3
    SPADES = 4
    TAROCK = 5

# Values:
# Tarock:
# 1,2,3,4,..,21,22
# Suits:
# 1,2,3,4, 5,6,7,8

class Card:
    suit: Suit
    value: int

    def __init__(self,
                 suit: Suit,
                 value: int,
                 ):
        self.suit = suit
        self.value = value
        assert isinstance(suit, Suit), 'Must specify suit'
        if suit == suit.TAROCK:
            assert 1 <= value <= 22, "Tarock have values between 1 and 22"
        else:
            assert 1 <= value <= 8, "Suits have values between 1 and 8"

    def __gt__(self, other):
        if not isinstance(other, Card):
            raise ValueError('Can only compare two cards.')
        if self.suit.value > other.suit.value:
            return True
        elif self.suit.value < other.suit.value:
            return False
        return self.value > other.value

    def __str__(self):
        return f"[{self.suit.name} {self.value}]"

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return self.suit.value*100 + self.value

    def enc_str(self):
        return f"{self.suit.name[0]!s}{self.value}"


    @staticmethod
    def dec_str(encstr: str):
        s = encstr.strip().split(" ")
        suit = int(s[0])
        val = int(s[1])
        return Card(Suit(suit), val)


class CardCollection(Set):
    cards: Set[Card]

    def __init__(self, cards: Iterable[Card] = None):
        super(CardCollection, self).__init__()
        if cards is not None:
            for card in cards:
                self.add(card)

    def __iter__(self):
        sorted_cards = list(super(CardCollection, self).__iter__())
        sorted_cards.sort()
        return iter(sorted_cards)

    def enc_list(self):
        enclist = list()
        for c in self:
            enclist.append(c.enc_str())
        return enclist

    @staticmethod
    def dec_list(enclist: List[str]):
        coll = CardCollection()
        for encstr in enclist:
            card = Card.dec_str(encstr)
            coll.add(card)
        return coll

    def point_value(self):
        points = 0
        for c in self:
            if c.suit is not Suit.TAROCK:
                if c.value > 4:
                    points += c.value - 3
                else:
                    points += 1
            else:
                if c.value in (1, 21, 22):
                    points += 5
                else:
                    points += 1
        points -= 2*(len(self) // 3)
        blatt = len(self) % 3
        points -= blatt
        return points, blatt


def get_full_deck() -> CardCollection:
    deck = CardCollection()
    for suit in Suit:
        if suit is not Suit.TAROCK:
            maxval = 8
        else:
            maxval = 22
        for val in range(1, maxval+1):
            deck.add(Card(suit, val))
    return deck


