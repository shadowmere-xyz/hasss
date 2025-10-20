import base64
import re
import time

import click
import requests
from requests.exceptions import SSLError, ReadTimeout
from urllib3.exceptions import MaxRetryError


@click.command()
@click.argument(
    "list_url",
    required=True,
)
@click.option("--test", is_flag=True, help="Wether to test the proxies found.")
@click.option(
    "--shadowtest-url",
    help="The shadowtest instance to use.",
    default="https://shadowtest.akiel.dev",
)
def probe(list_url: str, test: bool, shadowtest_url: str) -> None:
    """Check if a proxy list has shadowsocks proxies."""
    click.secho(
        "=== Checking proxies for shadowsocks === "
        + "\nList URL: "
        + click.style(list_url, fg="blue")
        + f"\nTest proxies: {click.style(str(test), fg='blue')}"
        + f"\nShadowtest: {click.style(shadowtest_url, fg='blue')}"
        + "\n========================================\n",
    )
    r = requests.get(list_url)
    if r.status_code != 200:
        click.echo(click.style(f"Failed to fetch the list: {r.status_code}", fg="red"))
        return

    lines = r.text.splitlines()

    if re.match(
        r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$",
        r.text,
        re.IGNORECASE,
    ):
        click.echo(
            "The list appears to be "
            + click.style("base64", fg="red")
            + " encoded. Decoding..."
        )
        try:
            decoded = base64.b64decode(r.text)
            lines = [line.decode("utf-8") for line in decoded.splitlines()]
        except Exception as e:
            click.echo(f"Failed to decode the list: {e}")
            return

    proxies = [p for p in lines if p.startswith("ss://")]
    if len(proxies) > 0:
        click.echo(
            f"Found {click.style(str(len(proxies)), fg='blue')} shadowsocks proxies"
        )
    else:
        click.echo(click.style("No shadowsocks proxies found!", fg="red"))

    active_count = 0
    if test and len(proxies) > 0:
        click.echo("Testing proxies...")
        for proxy in proxies:
            click.echo(
                click.style(
                    f"Testing proxy {proxies.index(proxy) + 1}/{len(proxies)} -- active: {active_count}",
                    fg="cyan",
                ),
                nl=False,
            )
            click.echo("\r", nl=False)
            try:
                proxy_info_request = requests.post(
                    f"{shadowtest_url}/v2/test", json={"address": proxy}
                )
            except (SSLError, ReadTimeout, MaxRetryError) as e:
                continue
            if proxy_info_request.status_code != 200:
                continue
            proxy_info = proxy_info_request.json()
            if (
                "YourFuckingIPAddress" in proxy_info
                and proxy_info["YourFuckingIPAddress"] != ""
            ):
                active_count += 1
            time.sleep(0.2)

        click.echo(
            f"Found {click.style(str(active_count), fg='red' if active_count == 0 else 'blue')} active shadowsocks proxies"
        )


if __name__ == "__main__":
    probe()
