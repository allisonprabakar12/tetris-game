from aiohttp import web, WSMsgType
import aiohttp, asyncio
import copy
import random 

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

def choose_moves(data):
   board = data.get("board")
   if board is None:
       return ['drop']
   shape_id = data["next"]
   best_move = None
   best_score = float('-inf')

   for rot, offsets in enumerate(shapes[shape_id]):
       min_dx = min(x for x, y in offsets)
       max_dx = max(x for x, y in offsets)
       for x in range(-min_dx, 10 - max_dx):
           y = 0
           while valid(board, shape_id, rot, x, y + 1):
               y += 1
           if not valid(board, shape_id, rot, x, y):
               continue

           sim = board[:]
           for dx, dy in offsets:
               cx, cy = x + dx, y + dy
               if 0 <= cy < 20:
                   sim[cy] |= shape_id << ((9 - cx) * 3)

           cleared = sum(
               1 for row in sim if all(((row >> (3 * i)) & 0b111) != 0 for i in range(10))
           )

           holes = 0
           for col in range(10):
               found = False
               for row in range(20):
                   val = (sim[row] >> (3 * (9 - col))) & 0b111
                   if val != 0:
                       found = True
                   elif found:
                       holes += 1

           heights = [
               20 - next((i for i in range(20) if ((sim[i] >> (3 * (9 - col))) & 0b111) != 0), 20)
               for col in range(10)
           ]

           bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(9))
           max_height = max(heights)

           score = (
               cleared * 200        
               - holes * 80         
               - bumpiness * 0.8    
               - max_height * 1.5   
               + x * 0.3            
           )

           if score > best_score:
               best_score = score
               best_move = (rot, x)
   if best_move is None:
       return ['drop']
   target_rot, target_x = best_move
   moves = []
   cur_rot, cur_x = 0, 4
   rot_diff = (target_rot - cur_rot) % len(shapes[shape_id])
   if rot_diff > 2:
       moves += ['ccw'] * (4 - rot_diff)
   else:
       moves += ['cw'] * rot_diff
   dx = target_x - cur_x
   moves += ['left'] * (-dx) if dx < 0 else ['right'] * dx
   moves.append('drop')
   return moves


def valid(board, s, o, x, y):
    for dx, dy in shapes[s][o]:
        nx, ny = x + dx, y + dy
        if not (0 <= nx < 10 and 0 <= ny < 20):
            return False
        if ((board[ny] >> (3 * (9 - nx))) & 0b111) != 0:
            return False
    return True

async def play_games(client, url):
    """Main game connection and play logic."""
    alltasks.add(asyncio.current_task())
    asyncio.current_task().add_done_callback(taskdone)
    try:
        while True:
            await asyncio.sleep(2) # pause between games; feel free to change this
            try: ws = await client.ws_connect(url)
            except:
                print('Game server at', url, 'did not let the bot play')
                return
            wsoftask[asyncio.current_task()] = ws
            print('Starting a new game')
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = msg.json() # parse message from server
                    
                    
                    # replace code starting here
                    if 'event' in data: # game over
                        print('EVENT:', data['event'])
                        await ws.close() # MUST keep this to avoid infinite wait on ended game
                    elif 'next' in data: # 'next' is given when a new tetromino appears
                        await asyncio.sleep(random.uniform(1.0, 2.0))  # pause to not look AI-like
                        moves = choose_moves(data)
                        for move in moves:
                            await asyncio.sleep(random.uniform(0.3, 0.6))
                            if random.random() < 0.98:
                                await ws.send_str(move) # take action
                    # replace code above here
                    
                    
                elif msg.type == WSMsgType.ERROR:
                    print(f'connection to {url} received {ws.exception()}')
            
    except BaseException as ex:
        print("Game terminated with exception:\n   ", type(ex),'\n   ', ex)


# Written by course staff. Do not edit.
routes = web.RouteTableDef()
alltasks = set() # track tasks we might need to cancel if the server stops
wsoftask = {}    # when a task opens a ws, that is added here

def taskdone(task):
    """Written by course staff. Do not edit.
    Helper method to clean up ws and tasks"""
    alltasks.discard(task)
    if task in wsoftask:
        asyncio.create_task(wsoftask[task].close())
        del wsoftask[task]

@routes.get('/')
async def get_html(request):
    """Written by course staff. Do not edit.
    Returns the HTML user interface"""
    return web.FileResponse("botui.html")

@routes.post('/server')
async def play_on_server(request):
    """Written by course staff. Do not edit.
    Connects the bot to a server"""
    url = await request.text()
    alltasks.add(asyncio.create_task(play_games(request.app['client'], url)))
    return web.Response(status=200, text="OK")

@routes.get('/stopall')
async def get_html(request):
    """Written by course staff. Do not edit.
    Returns the HTML user interface"""
    for task in tuple(alltasks):
        try: task.cancel()
        except: pass
    return web.Response(status=200, text="OK")


async def shutdown_ws(app):
    """Cleanup"""
    for task in tuple(alltasks):
        try: task.cancel()
        except: pass

async def startup_client(app):
    """A shared client for better DNS caching"""
    app['client'] = aiohttp.ClientSession()

async def shutdown_client(app):
    """Cleanup"""
    await app['client'].close()


def setup_app(app):
    """Register all the setup and cleanup callbacks"""
    app.on_startup.append(startup_client)
    app.on_shutdown.append(shutdown_ws)
    app.on_shutdown.append(shutdown_client)
    app.add_routes(routes)
    
if __name__ == '__main__': 
    app = web.Application()
    setup_app(app)
    web.run_app(app, host='0.0.0.0', port=41801) # this function never returns