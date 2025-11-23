import asyncio
import websockets

""" A 'simple' WEB Socket program that provides a console into grblHAL that
    runs over a network connection.  Set 'GRBLHAL_WS_URL' to point to grblHAL
    on the network.  Can be an IP number or network name.

    This console is almost identical to using a serial terminal console.  However,
    using web sockets is way faster and more stable and fault tolerant.
"""

# IP Number or network name for grblHAL on the network.
# GRBLHAL_WS_URL = "ws://192.168.50.200:81"
GRBLHAL_WS_URL = "ws://grblHAL.local:81"

# ANSI Color Codes
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
RESET   = "\033[0m"

# Update these to match your own color preferences.
errColor = RED          # Error Color
repColor = CYAN         # Response Color
infoColor = MAGENTA     # Info Color
warnColor = YELLOW      # Warning Color

# =============================================================================
async def send_commands(websocket):
    """Read commands from stdin and send them to grblHAL."""
    loop = asyncio.get_running_loop()

    print(f"{infoColor}Type grbl commands (e.g. $$, $X, ?, G0 X10) or 'quit' to exit.{RESET}")
    while True:
        # non-blocking input
        # cmd = await loop.run_in_executor(None, input, "grbl> ")
        cmd = await loop.run_in_executor(None, input, f"{RESET}")

        if cmd.lower() in ("quit", "exit"):
            print(f"{infoColor}Closing connection...{RESET}")
            await websocket.close()
            break

        # grbl expects newline-terminated commands
        await websocket.send(f"{cmd}\n")


# =============================================================================
async def receive_responses(websocket):
    """Print all responses from grblHAL."""
    try:
        async for message in websocket:
            # grbl often sends multiple lines; just print them as-is
            print(f"{repColor}{message.strip()}{RESET}")

    except websockets.exceptions.ConnectionClosed as e:
        # Treat normal code 1000 and 1006 as a normal shutdown.
        if e.code in (1000, 1006):
            print(f"{warnColor}Connection closed normally (code={e.code}).{RESET}")
        else:
            print(f"{errColor}Connection closed (code={e.code}, reason={e.reason}){RESET}")


# =============================================================================
async def main():
    print(f"{MAGENTA}Connecting to {GRBLHAL_WS_URL} ...{RESET}")

    async with websockets.connect(GRBLHAL_WS_URL) as websocket:
        print(f"{infoColor}Connected to grblHAL WebSocket server.{RESET}")

        sender = asyncio.create_task(send_commands(websocket))
        receiver = asyncio.create_task(receive_responses(websocket))

        done, pending = await asyncio.wait(
            {sender, receiver},
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()


# =============================================================================
if __name__ == "__main__":
    asyncio.run(main())
