import asyncio
from pyartnet import ArtNetNode

from src.game import Game

async def fade(channel, color, duration):
    channel.add_fade(color, duration)
    await asyncio.sleep(duration / 1000)

async def updateArtnet(game: Game, channels):
    while True:
        if not game.running:
            continue
        await game.grid.update_artnet(channels)
        await asyncio.sleep(1 / 60)

async def main():
    # Run this code in your async function
    node = ArtNetNode('192.168.0.50', 6454)

    # Create universe 1~4
    universes = [node.add_universe(x) for x in range(0, 4)]

    channels = [universes[x].add_channel(1, 192) for x in range(4)]

    game = Game(16)
    asyncio.create_task(updateArtnet(game, channels))
    await game.run()

    # intensity = 0
    # values = [[], [], [], []]
    # for i in range(256):
    #     index = i // 64
    #     values[index].append(intensity)
    #     values[index].append(intensity)
    #     values[index].append(intensity)
    #     intensity += 1

    # channels[0].set_values(values[0])
    # channels[1].set_values(values[1])
    # channels[2].set_values(values[2])
    # channels[3].set_values(values[3])
    # await asyncio.sleep(1 / 60)

    # channels[3].set_values([255 if x == 0 else 0 for x in range(192)])
    # await asyncio.sleep(1 / 60)

if __name__ == '__main__':
    asyncio.run(main())