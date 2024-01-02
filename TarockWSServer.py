#!/usr/bin/env python
# *-* encoding: utf-8 *-*

import websockets
import asyncio
import logging
import argparse
import json
from typing import Optional, Dict
from tarockgame.game import GameType, Game, IllegalPlay, GameStage, Suit, Card
from collections import defaultdict, deque
from random import choice
from prometheus_client import start_http_server, Summary, Gauge, Counter


PYTAROCK_PLAYERS = Gauge(name='pytarock_players', documentation='Number of players connected')
PYTAROCK_TABLES = Gauge(name='pytarock_tables', documentation='Number of active tables')

logger = logging.getLogger(__name__)

def _(msg):
    return msg

class Table:
    players: list
    game: Optional[Game]

    def __init__(self):
        self.players = [None]*4
        self.game = Game(primary_player=0)

    async def send_state(self, playerIDs = range(4)):
        tasks = []
        for playerid in playerIDs:
            player = self.players[playerid]
            if player is None:
                continue
            else:
                old_state = player.data['state']
                msg = self.game.get_state_update(playerid=playerid, players=self.players, old_state=old_state)
                player.data['state'] = self.game.get_state(playerid=playerid, players=self.players)
                if msg:
                    tasks.append(asyncio.create_task(player.send(json.dumps(msg))))
        if tasks:
            await asyncio.wait(tasks)

    async def remove(self, player):
        if player.data['table'] != self:
            raise IllegalPlay('Player is not at this table')
        player.data['table'] = None
        i = self.players.index(player)
        self.players[i] = None
        await self.send_state()

    async def add(self, player):
        player.data = dict()
        if len(self) >= 4:
            raise IllegalPlay('This table is already full.')
        i = choice([idx for idx in range(4) if self.players[idx] is None])
        self.players[i] = player
        player.data['table'] = self
        player.data['name'] = f'Spieler {i+1}'
        player.data['i'] = i
        player.data['state'] = {}
        await self.send_state()

    def __len__(self):
        return sum([0 if x is None else 1 for x in self.players])

    def __bool__(self):
        return len(self) != 0

class WSGame:
    tables: Dict[str, Table]
    gametype_strings = {'positive': GameType.POSITIVE,
                        'negative': GameType.NEGATIVE,
                        'colorgame': GameType.COLORGAME,
                        'sechserdreier': GameType.SECHSERDREIER}
    suits = {'H': Suit.HEARTS,
             'C': Suit.CLUBS,
             'S': Suit.SPADES,
             'D': Suit.DIAMONDS,
             'T': Suit.TAROCK}

    def __init__(self):
        self.tables = defaultdict(Table)

    async def unregister(self, websocket):
        if websocket.data['table'] is not None:
            await websocket.data['table'].remove(websocket)
            PYTAROCK_PLAYERS.dec()
        websocket.data['table'] = None
        for tablename in list(self.tables.keys()):
            if not self.tables[tablename]:
                logger.debug(f'Deleted table "{tablename}"')
                del self.tables[tablename]
        PYTAROCK_TABLES.set(len(self.tables))

    async def user_exception(self, websocket, msg):
        task = asyncio.create_task(websocket.send(json.dumps({'alertmsg': msg})))
        await asyncio.wait([task])

    async def register(self, websocket, path: str):
        name = path.split('/')[-1]
        if not name:
            raise IllegalPlay('Table name must not be empty.')
        websocket.data = dict()
        table = self.tables[name]
        PYTAROCK_TABLES.set(len(self.tables))
        await table.add(websocket)
        PYTAROCK_PLAYERS.inc()
        logger.debug(f'Current tables: {self.tables.keys()!s}')

    async def __call__(self, websocket, path):
        # register(websocket) sends user_event() to websocket
        try:
            await self.register(websocket, path)
        except IllegalPlay as ex:
            await self.user_exception(websocket, str(ex))
        try:
            async for message in websocket:
                data = json.loads(message)
                logger.debug(f"event: {data}")
                table = websocket.data['table']
                try:
                    if 'my_name' in data:
                        websocket.data['name'] = data['my_name']
                    if 'ouvert' in data:
                        if websocket.data['i'] != table.game.primary_player:
                            raise IllegalPlay('Only the primary player can select ouvert.')
                        ouvert = data['ouvert']
                        table.game.set_ouvert(ouvert)
                    if 'select_gametype' in data:
                        if websocket.data['i'] != table.game.primary_player:
                            raise IllegalPlay('Only the primary player can select the game type.')
                        gametype = self.gametype_strings[data['select_gametype']]
                        table.game.set_game_type(gametype)
                    if 'take_talon' in data:
                        table.game.take_talon(websocket.data['i'], data['take_talon'])
                    if 'move' in data:
                        card_s = data['move']
                        card = Card(suit=self.suits[card_s[0]], value=int(card_s[1:]))
                        table.game.play_card(websocket.data['i'], card)
                    if 'autoplay' in data:
                        a = True
                        while a:
                            a = table.game.autoplay()
                            await table.send_state()
                            await asyncio.sleep(0.1)
                    if 'teams' in data:
                        teams = data['teams']
                        teams1 = deque(teams[:4])
                        teams1.rotate(websocket.data['i'])
                        table.game.teams = list(teams1) + teams[4:]
                        table.game.calculate_score()
                    if 'new_game' in data:
                        if table.game.game_stage != GameStage.POSTGAME:
                            raise IllegalPlay('Game is not finished yet.')
                        new_primary = (table.game.primary_player + 1) % 4
                        table.game = Game(primary_player=new_primary)
                    if 'finish_game' in data:
                        if table.game.primary_player != websocket.data['i']:
                            raise IllegalPlay('Only the primary player can end the game.')
                        table.game.game_stage = GameStage.POSTGAME
                        table.game.calculate_score()

                    await table.send_state()

                except IllegalPlay as ex:
                    await self.user_exception(websocket, str(ex))

        finally:
            await self.unregister(websocket)


def get_args(args=None):
    parser = argparse.ArgumentParser(description='Start the Tarock WebSocket Server')
    parser.add_argument('host', type=str, default='localhost', nargs='?',
                        help='interface to listen to')
    parser.add_argument('port', type=int, default=31426, nargs='?',
                        help='port to listen on')
    parser.add_argument('--debug', action='store_true',
                        help='activate debug messages')

    return parser.parse_args(args=args)


def main(args=None):
    if args is None:
        args = get_args()
    debug_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=debug_level)

    logger.info(f'Starting server at {args.host!s}:{args.port!s}')


    mygame = WSGame()
    start_http_server(8000)
    start_server = websockets.serve(mygame, args.host, args.port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main(get_args())
