#!/usr/bin/env python
from dataclasses import dataclass
import re
import asyncio
from pathlib import Path

import click
import bs4
import discord


TITLE_FORMAT = re.compile(r'.*, (.*) turn (\d*)')


@dataclass
class DominionsTurn:
    name: str
    turn_number: int

    @classmethod
    def from_html(cls, html):
        out = bs4.BeautifulSoup(html, features='html.parser')
        match = TITLE_FORMAT.match(out.title.text)
        if match:
            return cls(name=match.group(1), turn_number=match.group(2))

    def __repr__(self):
        return f"Turn {self.turn_number} of the Dominions 5 game {self.name} has started"



async def file_watcher(file_name, sleep_time=3):
    last_modified_time = None
    while True:
        await asyncio.sleep(sleep_time)
        status_file = Path(file_name)
        current_modified_time = status_file.stat().st_mtime
        if current_modified_time != last_modified_time:
            yield status_file.read_text()
        last_modified_time = current_modified_time


async def send_dom5_updates_to_discord(file, token, channel):
    try:
        client = discord.Client()
        await client.login(token)
        channel = await client.fetch_channel(channel)
        async for file_update in file_watcher(file):
            current_turn = DominionsTurn.from_html(file_update)
            history = [m.content for m in await channel.history(limit=100).flatten()]

            if str(current_turn) not in history:
                print("Sending discord message")
                await channel.send(str(current_turn))
            else:
                print("Skipping sending a message to discord we've already sent one for this turn")
            print(current_turn)
    except Exception as e:
        raise e
    finally:
        await client.close()

@click.command()
@click.option("--scores-file", envvar="DOM5_SCORES_FILE", help="A file called scores.html, it is generated by the Dominions 5 server when it is run with the flag --statuspage", required=True)
@click.option("--discord-token", envvar="DISCORD_BOT_TOKEN", help="A valid Discod bot token", required=True)
@click.option("--discord-channel", envvar="DISCORD_CHANNEL", help="The discord channel to connect to, it should be the channel ID which is a large integer.", required=True)
def main(scores_file, discord_token, discord_channel):
    asyncio.run(send_dom5_updates_to_discord(scores_file, discord_token, discord_channel))

if __name__ == "__main__":
    main()
