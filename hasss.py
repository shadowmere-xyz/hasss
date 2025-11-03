import base64
import re
import sys
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
@click.option("--test", "-t", is_flag=True, help="Whether to test the proxies found.")
@click.option(
    "--bell",
    "-b",
    is_flag=True,
    help="Sound bell on first active proxy found and when finished.",
)
@click.option(
    "--shadowtest-url",
    "-u",
    help="The shadowtest instance to use.",
    default="https://shadowtest.akiel.dev",
)
@click.help_option("--help", "-h")
def probe(list_url: str, test: bool, bell: bool, shadowtest_url: str) -> None:
    """Check if a proxy list has shadowsocks proxies."""
    click.secho(
        "=== Checking proxies for shadowsocks === "
        + "\nList URL: "
        + click.style(list_url, fg="blue")
        + f"\nTest proxies: {click.style(str(test), fg='blue')}"
        + f"\nShadowtest: {click.style(shadowtest_url, fg='blue')}"
        + f"\nSound 🔔: {click.style(str(bell), fg='blue')}"
        + "\n========================================\n",
    )
    proxies = get_proxies(list_url)
    if len(proxies) > 0:
        click.echo(
            f"Found {click.style(str(len(proxies)), fg='blue')} shadowsocks proxies"
        )
    else:
        error_and_exit("No shadowsocks proxies found!")

    if test and len(proxies) > 0:
        active_count = test_proxies(bell, proxies, shadowtest_url)

        click.echo(
            f"Found {click.style(str(active_count), fg='red' if active_count == 0 else 'blue')} active shadowsocks proxies"
        )
    if bell:
        click.echo("\a", nl=False)


def get_proxies(list_url: str) -> list[str]:
    """
    Fetch and parse the proxy list from the given URL.
    :param list_url: the URL of the proxy list
    :return: a list of shadowsocks proxies
    """
    r = requests.get(list_url)
    if r.status_code != 200:
        error_and_exit(f"Failed to fetch the list: {r.status_code}")

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
            error_and_exit(f"Failed to decode the list: {e}")

    return [p for p in lines if p.startswith("ss://")]


def test_proxies(bell: bool, proxies: list[str], shadowtest_url: str) -> int:
    """
    Test the given list of proxies using the shadowtest instance.
    :param bell: whether to sound a bell on first active proxy found
    :param proxies: list of proxies to test
    :param shadowtest_url: the shadowtest instance URL
    :return: number of active proxies found
    """
    active_count = 0

    with click.progressbar(proxies, label="testing proxies") as proxies_list:
        for proxy in proxies_list:
            proxies_list.label = f"Testing proxies (active: {active_count})"
            try:
                proxy_info_request = requests.post(
                    f"{shadowtest_url}/v2/test", json={"address": proxy}
                )
            except (SSLError, ReadTimeout, MaxRetryError):
                continue
            if proxy_info_request.status_code != 200:
                continue
            proxy_info = proxy_info_request.json()
            if (
                "YourFuckingIPAddress" in proxy_info
                and proxy_info["YourFuckingIPAddress"] != ""
            ):
                active_count += 1
                if active_count == 1 and bell:
                    click.echo("\a", nl=False)
            time.sleep(0.2)
    return active_count


def error_and_exit(message: str) -> None:
    click.echo(click.style(message, fg="red"))
    sys.exit(1)


if __name__ == "__main__":
    probe()
