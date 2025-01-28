import asyncio
import typing


async def periodic_call(
    awaitable: typing.Callable[[], typing.Awaitable],
    stop_event: asyncio.Event,
    interval=10,
):
    while not stop_event.is_set():
        await awaitable()

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                interval,
            )
        except asyncio.TimeoutError:
            pass
