import jwt
import time
import aiohttp
import requests
import datetime


class GithubAPIError(Exception):
    pass


class GithubRequestsManager:
    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        app_id: str,
        private_key: str,
        installation_id: str,
        session: aiohttp.ClientSession = None,
    ) -> None:
        self.app_id = app_id
        self.private_key = private_key
        self.installation_id = installation_id
        self.session = session or aiohttp.ClientSession()

        self.token: str = None
        self.token_expires_at: datetime.datetime | None = None
        self.update_access_token()

    def get_jwt(self) -> str:
        """
        Gets the JWT for the app.

        Returns:
            str: The JWT.
        """

        return jwt.encode(
            {
                "iat": int(time.time()),
                "exp": int(time.time()) + (10 * 60),  # 10 minutes
                "iss": self.app_id,
            },
            self.private_key,
            algorithm="RS256",
        )

    def update_access_token(self) -> str:
        """
        Updates the installation access token using requests.

        Returns:
            str: The installation access token.
        """

        jwt = self.get_jwt()

        endpoint = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"

        headers = {
            "Authorization": f"Bearer {jwt}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.post(endpoint, headers=headers)

        if response.status_code == 201:
            data = response.json()
            self.token = data["token"]
            self.token_expires_at = datetime.datetime.fromisoformat(
                data["expires_at"][:-1]
            )
        else:
            raise GithubAPIError(
                f"Error updating access_token: {response.status_code} {response.text}"
            )

    async def async_update_access_token(self) -> str:
        """
        Updates the installation access token asynchronously.

        Returns:
            str: The installation access token.
        """

        jwt = self.get_jwt()

        endpoint = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"

        headers = {
            "Authorization": f"Bearer {jwt}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with self.session.post(endpoint, headers=headers) as response:
            if response.status == 201:
                data = await response.json()
                self.token = data["token"]
                self.token_expires_at = datetime.datetime.fromisoformat(
                    data["expires_at"][:-1]
                )
            else:
                raise GithubAPIError(
                    f"Error: {response.status} {await response.text()}"
                )

    @property
    def headers(self) -> dict:
        """
        Gets the headers to use for requests.

        Returns:
            dict: The headers.
        """

        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def refresh_token(self) -> None:
        """
        Refreshes the installation access token if it has expired.
        """

        if self.token_expires_at < datetime.datetime.utcnow():
            await self.async_update_access_token()

    async def get(self, endpoint: str) -> dict:
        """
        Sends a GET request to the given endpoint.

        Args:
            endpoint (str): The endpoint to send the request to.

        Returns:
            dict: The response data.
        """
        await self.refresh_token()

        endpoint = self.BASE_URL + endpoint
        async with self.session.get(endpoint, headers=self.headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise GithubAPIError(
                    f"Error: {response.status} {await response.text()}"
                )

    async def post(self, endpoint: str, data: dict) -> dict:
        """
        Sends a POST request to the given endpoint.

        Args:
            endpoint (str): The endpoint to send the request to.
            data (dict): The data to send.

        Returns:
            dict: The response data.
        """

        await self.refresh_token()

        endpoint = self.BASE_URL + endpoint
        async with self.session.post(
            endpoint, headers=self.headers, json=data
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise GithubAPIError(
                    f"Error: {response.status} {await response.text()}"
                )
