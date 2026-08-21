import asyncio
from aiogram.fsm.state import State
s = State("my_state")
async def main():
    print(s(None, raw_state="my_state"))
    print(s(None, raw_state=None))
asyncio.run(main())
