import asyncio
import websockets

connected_users = set()

async def sync_handler (websocket):
    connected_users.add(websocket)
    print(f"New user connected. Total users: {len(connected_users)}")
    try:
        async for message in websocket:
            print(f"Command received:{message}")
            
            for user in connected_users:
                if user != websocket:
                    await user.send(message)

    finally:
        connected_users.remove(websocket)
        print(f"User left. Total users: {len(connected_users)}")

async def start_server():
    print("SyncTheatre Server running on ws://localhost:8765")
    async with websockets.serve(sync_handler, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(start_server())
    