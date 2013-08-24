import urllib2
import logging

from lxml import html

# Default logger
logger = logging.getLogger('spotify2piratebay')


def fetch_url(url):
    """ Fetches a URL and returns contents - use opener to support HTTPS. """

    # Fetch and parse
    logger.debug(u'Fetching %s', url)

    # Use urllib2 directly for enabled SSL support (LXML doesn't by default)

    try:
        timeout = 30

        opener = urllib2.urlopen(url, None, timeout)

        # Fetch HTTP data in one batch, as handling the 'file-like' object to
        # lxml results in thread-locking behaviour.
        htmldata = opener.read()
    except urllib2.URLError:
        # Probably a timeout, try again
        htmldata = fetch_url(url)

    return htmldata


def parse_url(url):
    """
    Return lxml-parsed HTML for given URL or None when HTTP request failed.

    Uses urllib2 directly and fetches as string before parsing as to prevent
    thread locking issues.
    """
    htmldata = fetch_url(url)

    # No data, return None
    if not htmldata:
        return None

    # Parse
    logger.debug(u'Parsing HTML for %s', url)
    parsed = html.fromstring(htmldata, base_url=url)

    # Make all links in the result absolute
    parsed.make_links_absolute(url)

    return parsed
