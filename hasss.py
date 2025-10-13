import base64
import re

import click
import requests


@click.command()
@click.argument("list_url", required=True, )
def probe(list_url: str):
    """Check if a proxy list has shadowsocks proxies."""
    r = requests.get(list_url)
    if r.status_code != 200:
        click.echo(f'Failed to fetch the list: {r.status_code}')
        return

    proxies = r.text.splitlines()

    if re.match(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$', r.text, re.IGNORECASE):
        click.echo('The list appears to be base64 encoded. Decoding...')
        try:
            decoded = base64.b64decode(r.text)
            proxies = [line.decode('utf-8') for line in decoded.splitlines()]
        except Exception as e:
            click.echo(f'Failed to decode the list: {e}')
            return

    count = sum(1 for p in proxies if p.startswith('ss://'))
    if count:
        click.echo(f'Found {count} shadowsocks proxies')
    else:
        click.echo('No shadowsocks proxies found')


if __name__ == '__main__':
    probe()
