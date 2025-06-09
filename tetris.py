from aiohttp import web, WSMsgType
import asyncio
import random
import tilestub
from aiohttp.web import FileResponse


routes = web.RouteTableDef()

playws = {} # used to track open websockets to support graceful shutdown on Ctrl+C
watchws = set()
watchmap = {}
shapes = {
    1: [[[0,0],[1,0],[0,-1],[1,-1]]],
    2: [[(0,0),(0,-1),(0,-2),(0,-3)], [(-1,0),(0,0),(1,0),(2,0)]],
    3: [[(-1,-1),(0,-1),(1,-1),(0,0)], [(-1,-1),(0,-1),(0,-2),(0,0)],
        [(-1,0),(0,0),(1,0),(0,-1)], [(0,0),(0,-1),(0,-2),(1,-1)]],
    4: [[(0,-2),(0,-1),(0,0),(1,0)], [(0,0),(0,-1),(1,-1),(2,-1)],
        [(-1,-2),(0,-2),(0,-1),(0,0)], [(-1,0),(0,0),(1,0),(1,-1)]],
    5: [[(-1,0),(0,0),(0,-1),(0,-2)], [(0,-1),(0,0),(1,0),(2,0)],
        [(0,0),(0,-1),(0,-2),(1,-2)], [(-1,-1),(0,-1),(1,-1),(1,0)]],
    6: [[(0,-2),(0,-1),(1,-1),(1,0)], [(-1,0),(0,0),(0,-1),(1,-1)]],
    7: [[(1,-2),(1,-1),(0,-1),(0,0)], [(-1,-1),(0,-1),(0,0),(1,0)]]
}

async def send_to(ws, msg):
    await ws.send_json(msg)
    for watcher, target_id in watchmap.items():
        if target_id == id(ws):
            try:
                await watcher.send_json(msg)
            except:
                pass  # ignore broken watchers


class TetrisGame:
    def __init__(self, ws):
        self.ws = ws
        self.board = [0]*20
        self.next = tilestub.new_tile()
        self.spawn()
        self.task = asyncio.create_task(self.fallLoop())

    def spawn(self):
        s = self.next
        o = 0
        x = 4
        min_dy = min(dy for _, dy in shapes[s][o])
        start_y = -min_dy
        for y in range(start_y, 20):
            if self.valid(s, o, x, y):
                self.live = (s, o, x, y)
                self.next = tilestub.new_tile()
                self.send(include_board=True)
                return
        asyncio.create_task(self.ws.send_json({"event": "gameover"}))
        self.task.cancel()
            

    def valid(self, s, o, x, y):
        for dx, dy in shapes[s][o]:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < 10 and 0 <= ny < 20):
                return False
            cell = (self.board[ny] >> ((9 - nx) * 3)) & 0b111
            if cell != 0:
                return False
        return True

    def fall(self):
        s, o, x, y = self.live
        if self.valid(s, o, x, y + 1):
            self.live = (s, o, x, y + 1)
            self.send()
        else:
            for dx, dy in shapes[s][o]:
                cx, cy = x + dx, y + dy
                if 0 <= cy < 20:
                    self.board[cy] |= s << ((9 - cx) * 3)
            self.clear()
            self.send(include_board=True)
            self.spawn()

    def drop(self):
        s, o, x, y = self.live
        while self.valid(s, o, x, y + 1):
            y += 1
        self.live = (s, o, x, y)
        self.fall()

    def clear(self):
        self.board = [row for row in self.board if any(((row >> (3*i)) & 0b111) == 0 for i in range(10))]
        self.board = [0] * (20 - len(self.board)) + self.board

    def move(self, dx):
        s, o, x, y = self.live
        if self.valid(s, o, x + dx, y):
            self.live = (s, o, x + dx, y)
            self.send()
    
    def rotate(self, dir):
        s, o, x, y = self.live
        no = (o + dir) % len(shapes[s])

        if self.valid(s, no, x, y):
            self.live = (s, no, x, y)
            self.send()
            return True
        
        kick_allowed = False
        for dx, dy in shapes[s][no]:
            nx, ny = x + dx, y + dy
            if nx <= 0 or nx >= 9 or ny < 0:
                kick_allowed = True
                break

        if kick_allowed:
            if self.valid(s, no, x, y + 1):
                self.live = (s, no, x, y + 1)
                self.send()
                return True

            for shift in [1, -1, 2, -2]:
                if self.valid(s, no, x + shift, y):
                    self.live = (s, no, x + shift, y)
                    self.send()
                    return True
        return False

    def dropDistance(self):
        s, o, x, y = self.live
        d = 0
        while self.valid(s, o, x, y + d + 1):
            d += 1
        return d

    def send(self, event = None, include_board=False):
        s, o, x, y = self.live

        msg = {
            "live": [s, o, x, y, self.dropDistance()],
            "next": self.next,
           
        }
        if include_board or event == "lock":
            msg["board"] = self.board
        if event:
            msg["event"] = event
        asyncio.create_task(send_to(self.ws, msg))

    async def fallLoop(self):
        try:
            while True:
                await asyncio.sleep(0.5)
                self.fall()
        except asyncio.CancelledError:
            pass
    
    def cancel(self):
        self.task.cancel()




@routes.get('/ws')
async def websocket_handler(request : web.Request) -> web.WebSocketResponse:
    """The main event loop: accepts connections, manages games, cleans up"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    playws[id(ws)] = ws
    
    ... # FIX ME: initialize a game for this websocket
    game = TetrisGame(ws)

    async for msg in ws:
        
        if msg.type == WSMsgType.TEXT:
             # FIX ME: process user event from msg.data
            if msg.data == 'left': game.move(-1)
            elif msg.data == 'right': game.move(1)
            elif msg.data == 'down': game.fall()
            elif msg.data == 'drop': game.drop()
            elif msg.data == 'cw': game.rotate(1)
            elif msg.data == 'ccw': game.rotate(-1)
        
        elif msg.type == WSMsgType.ERROR:
            print(f'WebSocket received exception {ws.exception()}')
    game.task.cancel()
    del playws[id(ws)]
    return ws

@routes.get('/watch')
async def watch_html(req: web.Request) -> web.FileResponse:
    return FileResponse(path="watch.html")

@routes.get('/snoop')
async def snoop(req: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(req)
    watchws.add(ws)

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == "?":
                    await ws.send_json({"alive": list(playws.keys())})
                elif msg.data.isdigit() and int(msg.data) in playws:
                    watchmap[ws] = int(msg.data)
            elif msg.type == WSMsgType.ERROR:
                print("Watcher error:", ws.exception())
    finally:
        watchws.discard(ws)
        watchmap.pop(ws, None)

    return ws


@routes.get('/')
async def index(req : web.Request) -> web.FileResponse:
    """A simple method for sharing the index.html with players"""
    return FileResponse(path="index.html")

async def shutdown_ws(app: web.Application) -> None:
    """Ctrl+C won't work right unless we close any open websockets,
    so this function does that."""
    for other in tuple(playws):
        await playws[other].close()
    for watcher in tuple(watchws):
        await watcher.close()

def setup_app(app: web.Application) -> None:
    """Registers routes and any setup and shutdown handlers needed
    The default provided with the MP is probablt sufficient"""
    app.on_shutdown.append(shutdown_ws)
    app.add_routes(routes)
    
# To facilitate testing, do not change anything below this line
if __name__ == '__main__': 
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default="0.0.0.0")
    parser.add_argument('-p','--port', type=int, default=10340)
    args = parser.parse_args()

    app = web.Application()
    setup_app(app)
    web.run_app(app, host=args.host, port=args.port) # this function never returns