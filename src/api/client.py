from loguru import logger
from aiohttp import ClientSession, ClientResponse


class APIRequestFailed(Exception):
    def __init__(self, response: ClientResponse):
        self.response = response
        super.__init__()


class APIClient:
    def __init__(self, url: str, token: str) -> None:
        """An API client to connect to the maelstrom API.

        Args:
            url (str): The API url to connect to.
            token (str): The token to use for requests.
        """

        self.url = url
        self.token = token

        self.session: ClientSession = None

    async def setup(self) -> None:
        """Create the client session."""

        self.session = ClientSession(headers={
            "X-Api-Token": self.token,
        })

    async def request(self, method: str, path: str, **kwargs):
        """Make an API request to the maelstrom API.

        Args:
            method (str): The HTTP method to use.
            path (str): The path to request.
        """

        if not self.session or self.session.closed:
            await self.setup()

        for i in range(3):
            response = await self.session.request(method, self.url + path, **kwargs)

            if 200 <= response.status < 300:
                return await response.json()

            logger.warning(f"API returned response code {response.status} on route {path}")

        logger.error(f"API failed 3 times on route {path} with final response code {response.status}")
        raise APIRequestFailed(response)
