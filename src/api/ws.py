from os import getenv
from asyncio import sleep

from loguru import logger
from aiohttp import WSMsgType

from .client import APIClient


class WSClient:
    def __init__(self, client: APIClient, bot) -> None:
        """A persistent websocket connection to the API.

        Args:
            client (APIClient): The API client to use.
            bot (Bot): The bot to use.
        """

        self.client = client
        self.bot = bot

        self.handlers = {}
        self.connection = None

    async def stayalive(self):
        while True:
            try:
                await self.connect()
            except Exception as e:
                logger.error(f"Error while connecting to the API websocket: {e}")
            finally:
                self.connection = None
            await sleep(1)

    async def connect(self):
        if not self.client.session or self.client.session.closed:
            await self.client.setup()

        await self.bot.wait_until_ready()

        logger.info("Connecting to API websocket...")

        self.connection = await self.client.session.ws_connect(
            getenv("API_WS_URL"),
            max_msg_size=0,
            headers={
                "Authorization": getenv("API_TOKEN")
            }
        )

        logger.info("API websocket connected.")

        async for message in self.connection:
            if message.type == WSMsgType.TEXT:
                data = message.json()

                if data["op"] == "expect":
                    await self.handle_expect(data["d"])

        logger.info(f"API websocket has disconnected with code {self.connection.close_code}.")

    async def send(self, status: str, data: dict) -> None:
        await self.connection.send_json({
            "status": status,
            **data,
        })

    async def handle_expect(self, data: dict) -> None:
        rt, rp = data["type"], data["params"]

        if rt == "guild_member_permissions":
            guild_id = rp["guild"]
            member_id = rp["member"]
            permission = rp["permission"]

            guild = self.bot.get_guild(guild_id)
            if not guild:
                return await self.send("guild_not_found")

            member = guild.get_member(member_id)
            if not member:
                return await self.send("member_not_found")

            return await self.send("ok", {
                "value": getattr(member.guild_permissions, permission)
            })
