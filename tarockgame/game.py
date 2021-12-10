from .cards import Card, CardCollection, get_full_deck, Suit
from typing import Optional, List, Tuple, Dict
from enum import Enum
import random
from collections import deque


class IllegalPlay(Exception):
    def __init__(self, msg, *args):
        Exception.__init__(self, msg, *args)

def _(msg):
    return msg

class Player:
    id: int
    hand_cards: CardCollection
    taken_cards: List[List[Card]]
    name: Optional[str] = None
    state: Dict = {}

    def __init__(self,
                 playerid: Optional[int] = None,
                 hand_cards: CardCollection = None,
                 taken_cards: List[List[Card]] = None,
                 ):
        self.id = playerid
        if hand_cards is None:
            self.hand_cards = CardCollection()
        else:
            self.hand_cards = hand_cards
        if taken_cards is None:
            self.taken_cards = list()
        else:
            self.taken_cards = taken_cards


class GameType(Enum):
    POSITIVE = 0
    NEGATIVE = 1
    COLORGAME = 2
    SECHSERDREIER = 3

class GameStage(Enum):
    PREGAME = 0
    TYPESELECTED = 1
    TALONTAKEN = 2
    TALONRETURNED = 3
    INGAME = 4
    POSTGAME = 5

    def __le__(self, other):
        return self.value <= other.value

    def __lt__(self, other):
        return self.value < other.value


class Table:
    talons_in_center: List[Optional[bool]]
    center_cards: List[Card]
    talons_uncovered: bool
    move: Optional[int]

    def __init__(self):
        self.center_cards = [None]*4
        self.talons_in_center = [True]*2
        self.talons_uncovered = False
        self.move = None


class Game(Table):
    players: Tuple[Player, ...]
    primary_player: int
    talons: Optional[Tuple[CardCollection, CardCollection]]
    original_talons: Optional[Tuple[CardCollection, CardCollection]]
    game_type: Optional[GameType]
    move: Optional[int]
    game_stage: GameStage
    ausspieler = Optional[int]
    teams: Optional[List[int]]
    score: Optional[List[str]]
    single_score: Optional[List[str]]
    ouvert: bool
    stiche: int

    def __init__(self,
                 primary_player: int,
                 game_type: Optional[GameType] = None,
                 ):
        Table.__init__(self)
        players = list()
        for i in range(4):
            p = Player(playerid=i)
            players.append(p)
        self.players: Tuple[Player, ...] = tuple(players)
        self.primary_player = primary_player
        assert 0 <= primary_player < 4
        self.game_type = game_type
        self.deal_cards()
        self.move = None
        self.ausspieler = None
        self.game_stage = GameStage.PREGAME
        self.teams = [0]*6
        self.score = [""]*2
        self.single_score = [""]*6
        self.ouvert = False
        self.stiche = 0

    def deal_cards(self):
        deck = get_full_deck()
        for p in self.players:
            for _ in range(12):
                c = random.choice(list(deck))
                deck.remove(c)
                p.hand_cards.add(c)
        self.talons = (CardCollection(), CardCollection())
        self.original_talons = (CardCollection(), CardCollection())
        for t, t2 in zip(self.talons, self.original_talons):
            for _ in range(3):
                c = random.choice(list(deck))
                deck.remove(c)
                t.add(c)
                t2.add(c)
        assert len(deck) == 0

    def set_game_type(self, type: GameType):
        if self.game_stage > GameStage.PREGAME:
            raise IllegalPlay("Game Type can only be selected pre-game.")
        if type is GameType.SECHSERDREIER:
            self.game_type = GameType.POSITIVE
            self._transfer_talon(self.primary_player, 0)
            self._transfer_talon(self.primary_player, 1)
        else:
            self.game_type = type
            self.game_stage = GameStage.TYPESELECTED
        if self.game_type is not GameType.NEGATIVE:
            self.move = self.primary_player
            self.ausspieler = self.primary_player

    def set_ouvert(self, ouvert: bool):
        if self.game_stage > GameStage.PREGAME:
            raise IllegalPlay("Ouvert can only be selected pre-game.")
        self.ouvert = ouvert

    def finish_play(self):
        highest, highest_card = self._find_highest_card()
        self.players[highest].taken_cards.append(self.center_cards)
        self.ausspieler = highest
        self.move = highest
        self.stiche += 1

    def _find_highest_card(self, cards: List[Card] = None) -> (int, Card):
        if cards is None:
            cards = self.center_cards
        highest = self.ausspieler
        highest_card = cards[self.ausspieler]
        i_one = None
        i_twentyone = None
        for i, card in enumerate(cards):
            if card is None:
                continue
            if card == Card(Suit.TAROCK, 21):
                i_twentyone = i
            elif card == Card(Suit.TAROCK, 1):
                i_one = i
            if highest_card.suit == card.suit:
                if card.value > highest_card.value:
                    highest = i
                    highest_card = card
            elif card.suit is Suit.TAROCK and self.game_type is not GameType.COLORGAME:
                highest = i
                highest_card = card
        if highest_card == Card(Suit.TAROCK, 22) and i_one is not None and i_twentyone is not None:
            highest = i_one
        return highest, highest_card

    def autoplay(self):
        if self.move is None:
            return False
        for c in self.players[self.move].hand_cards:
            try:
                self.play_card(self.move, c)
            except IllegalPlay:
                pass
            else:
                return True
        return False

    def play_card(self,
                  playerid: int,
                  card: Card,
                  ):
        if self.game_stage < GameStage.TYPESELECTED:
            raise IllegalPlay('Game type needs to be selected before playing a card.')
        elif self.game_stage > GameStage.INGAME:
            raise IllegalPlay('Game is already over.')
        elif self.game_stage is GameStage.TALONTAKEN:
            if len(self.players[playerid].hand_cards) > 12:
                # Remove talon cards
                if card not in self.players[playerid].hand_cards:
                    raise IllegalPlay("You cannot play right now.")
                if (card.suit == Suit.TAROCK and (card.value in {1, 21, 22})) \
                        or (card.suit is not Suit.TAROCK and card.value == 8):
                    # Trull und Könige können nicht abgelegt werden.
                    raise IllegalPlay("You cannot drop this card.")

                if len(self.players[playerid].taken_cards) == 0:
                    self.players[playerid].taken_cards.append([])
                self.players[playerid].taken_cards[-1].append(card)
                self.players[playerid].hand_cards.remove(card)
                if len(self.players[playerid].hand_cards) == 12:
                    self.game_stage = GameStage.TALONRETURNED
            else:
                raise IllegalPlay("You cannot play before the talon is returned.")
        elif self.game_stage is GameStage.TYPESELECTED or self.game_stage is GameStage.TALONRETURNED:
            if self.move is None or self.move == playerid:
                if self.move is None:
                    assert self.ausspieler is None
                    self.ausspieler = playerid
                    self.move = playerid
                self.game_stage = GameStage.INGAME
                self.talons_in_center = [False]*2
            else:
                raise IllegalPlay("It is not your turn.")

        if self.game_stage is GameStage.INGAME:
            if self.move is not None and self.move != playerid:
                raise IllegalPlay("It is not your turn.")
            if card not in self.players[playerid].hand_cards:
                raise IllegalPlay("You do not have this card. Are you cheating?")
            if self.move == self.ausspieler:
                self.center_cards = [None]*4
            if not self._check_legal_play(playerid=playerid, card=card):
                raise IllegalPlay("You are not allowed to play this card.")
            self.center_cards[playerid] = card
            self.players[playerid].hand_cards.remove(card)
            self.move = (playerid + 1) % 4

            if len([x for x in self.center_cards if x is not None]) == 4:
                self.finish_play()
            self.is_finished()

    def is_finished(self) -> bool:
        if all([len(p.hand_cards) == 0 for p in self.players]):
            self.move = None
            self.game_stage = GameStage.POSTGAME
            self.calculate_score()
            return True
        else:
            return False

    def _check_legal_play(self,
                          playerid: int,
                          card: Card,
                          check_stichzwang=True) -> bool:
        if playerid == self.ausspieler:
            if self.game_type is GameType.COLORGAME:
                if card.suit is Suit.TAROCK:
                    for c in self.players[playerid].hand_cards:
                        if c.suit is not Suit.TAROCK:
                            return False
        else:
            # Farbzwang
            played_suit = self.center_cards[self.ausspieler].suit
            if card.suit is not played_suit:
                for c in self.players[playerid].hand_cards:
                    if c.suit is played_suit:
                        return False
                # Tarockzwang
                if played_suit is not Suit.TAROCK and card.suit is not Suit.TAROCK:
                    for c in self.players[playerid].hand_cards:
                        if c.suit is Suit.TAROCK:
                            return False

            if not check_stichzwang:
                return True

        if self.game_type is GameType.NEGATIVE:
            cards = self.center_cards.copy()
            cards[playerid] = card
            i_highest, _ = self._find_highest_card(cards)
            if i_highest != playerid:
                for c in self.players[playerid].hand_cards:
                    if c == card:
                        continue
                    if not self._check_legal_play(playerid, c, check_stichzwang=False):
                        continue
                    cards[playerid] = c
                    i_tmp, _ = self._find_highest_card(cards)
                    if i_tmp == playerid:
                        return False
            if card == Card(Suit.TAROCK, 1):
                has_other = False
                for c in self.players[playerid].hand_cards:
                    if c.suit is Suit.TAROCK and c.value > 1:
                        has_other = True
                        break
                if has_other and (Card(Suit.TAROCK, 22) not in self.center_cards or Card(Suit.TAROCK, 21) not in self.center_cards):
                    return False

        return True

    def uncover_talon(self, playerid: int):
        if playerid != self.primary_player:
            raise IllegalPlay('It needs to be your game to uncover the talon.')
        if self.talons_uncovered:
            raise IllegalPlay('The talon was already uncovered.')
        self.talons_uncovered = True

    def take_talon(self, playerid: int, talon_number: int):
        if self.game_stage < GameStage.TYPESELECTED:
            raise IllegalPlay('Game type needs to be selected before taking Talon.')
        if self.game_stage > GameStage.TALONTAKEN:
            raise IllegalPlay('Talon can only be taken before the game.')
        if not self.talons_in_center[talon_number]:
            raise IllegalPlay('This talon was already taken.')
        if self.game_type is GameType.NEGATIVE:
            raise IllegalPlay('The talon cannot be taken in negative games.')
        if not self.talons_uncovered:
            self.uncover_talon(playerid=playerid)
            return
        if not all(self.talons_in_center):
            raise IllegalPlay('Talon was already taken.')
        self._transfer_talon(playerid=playerid, talon_number=talon_number)

    def _transfer_talon(self, playerid: int, talon_number: int):
        self.game_stage = GameStage.TALONTAKEN
        self.talons_in_center[talon_number] = False
        for card in self.talons[talon_number]:
            self.players[playerid].hand_cards.add(card)
            self.talons[talon_number].remove(card)

    def calculate_score(self):
        if self.game_stage < GameStage.POSTGAME:
            raise IllegalPlay('Score can only be calculated after the game.')
        if self.teams is None:
            raise IllegalPlay('You have to select the teams first.')
        team_points = list()
        for i_team in range(2):
            cc = CardCollection()
            for i_player in range(4):
                if self.teams[i_player] == i_team:
                    for stich in self.players[i_player].taken_cards:
                        for c in stich:
                            cc.add(c)
            if self.teams[4] == i_team:
                cc |= self.talons[0]
            if self.teams[5] == i_team:
                cc |= self.talons[1]
            points = cc.point_value()
            team_points.append(points)
        self.score = team_points
        self.single_score = []
        for i in range(6):
            cc = CardCollection()
            if i < 4:
                for stich in self.players[i].taken_cards:
                    for c in stich:
                        cc.add(c)
            elif i == 4:
                cc |= self.talons[0]
            elif i == 5:
                cc |= self.talons[1]
            points = cc.point_value()
            self.single_score.append(points)

    def get_state(self, playerid, players):
        player = self.players[playerid]
        msg = {}

        hand = player.hand_cards.enc_list()
        msg['player_0'] = hand

        for i in range(1, 4):
            if self.ouvert and (self.stiche > 1 or
                                (self.stiche == 1and len([True for x in self.center_cards if x is not None]) in (1, 2, 3))):
                hand = self.players[(playerid + i) % 4].hand_cards.enc_list()
            else:
                hand = []
            msg[f'playerhand_{i!s}'] = hand

        talon_a = self.talons[0].enc_list()
        talon_b = self.talons[1].enc_list()

        # msg['talons_in_center'] = self.talons_in_center
        if self.talons_uncovered:
            msg['talon_a'] = talon_a
            msg['talon_b'] = talon_b
        else:
            msg['talon_a'] = [None] * len(talon_a)
            msg['talon_b'] = [None] * len(talon_b)

        if self.move is not None:
            msg['move'] = (self.move - playerid) % 4
        else:
            msg['move'] = None

        for i in range(4):
            card = self.center_cards[(i + playerid) % 4]
            center = [] if card is None else [card.enc_str()]
            msg[f"played_{i!s}"] = center

        if self.game_stage < GameStage.TYPESELECTED:
            msg['stage'] = 'pregame'
        elif self.game_stage < GameStage.TALONRETURNED:
            msg['stage'] = 'talon'
        elif self.game_stage < GameStage.POSTGAME:
            msg['stage'] = 'ingame'
        else:
            msg['stage'] = 'postgame'

        msg['taken_0'] = [[x.enc_str() for x in y] for y in self.players[playerid].taken_cards]

        if self.game_stage == GameStage.POSTGAME:
            taken_cards = []
            for i in range(4):
                j = (playerid + i) % 4
                taken = [[x.enc_str() for x in y] for y in self.players[j].taken_cards]
                taken_cards.append(taken)
            msg['taken_cards'] = taken_cards
            msg['post_talon_a'] = [x.enc_str() for x in self.talons[0]]
            msg['post_talon_b'] = [x.enc_str() for x in self.talons[1]]

            teams1 = deque(self.teams[:4])
            teams1.rotate(-playerid)
            msg['teams'] = list(teams1) + self.teams[4:]
            msg['score'] = self.score

            single_score1 = deque(self.single_score[:4])
            single_score1.rotate(-playerid)
            msg['single_score'] = list(single_score1) + self.single_score[4:]

        if self.game_type == GameType.NEGATIVE:
            stiche = deque([len(x.taken_cards) for x in self.players])
            stiche.rotate(-playerid)
            msg['stiche'] = list(stiche)


        player_names = []
        for j in range(4):
            k = (playerid + j) % 4
            p = players[k]
            if p is None:
                player_names.append(None)
            else:
                player_names.append(p.data['name'])

        msg['player_names'] = player_names

        msg['primary'] = (self.primary_player - playerid) % 4
        if self.game_type is None:
            msg['gametype'] = None
        elif self.game_type is GameType.NEGATIVE:
            msg['gametype'] = _("Negative")
        elif self.game_type is GameType.POSITIVE:
            msg['gametype'] = _("Positive")
        elif self.game_type is GameType.COLORGAME:
            msg['gametype'] = _("Colorgame")
        elif self.game_type is GameType.SECHSERDREIER:
            msg['gametype'] = _("Take all 6")

        return msg

    def get_state_update(self, playerid, players, old_state=None):
        if old_state is None:
            old_state = {}
        new_state = self.get_state(playerid=playerid, players=players)
        update = {}

        for key, value in new_state.items():
            if key not in old_state:
                update[key] = value
            else:
                if value != old_state[key]:
                    update[key] = value

        return update




