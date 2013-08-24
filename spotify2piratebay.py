#!/usr/bin/env python

import argparse, sys, logging, getpass, threading, codecs, urllib, os

from lxml import html

from spotify.manager import (
    SpotifySessionManager, SpotifyContainerManager, SpotifyPlaylistManager
)

from utils import parse_url

# Default logger
logger = logging.getLogger('spotify2piratebay')

# Threading humbug
container_loaded = threading.Event()

def pirate_search(term, category=0, sortorder=99):
    quoted_term = urllib.quote(term.encode('utf8'))

    url = 'https://thepiratebay.sx/search/%s/0/%d/%d' % (
        quoted_term, sortorder, category
    )

    page = parse_url(url)

    try:
        results = page.xpath('//*[@id="searchResult"]/tr')

        if not results:
            logger.warning('No torrent found for %s', term)
            logger.debug(html.tostring(page.body))

        torrents = []

        for result in results:
            torrent = {
                'name': result.xpath('td/div[@class="detName"]/a/text()')[0],
                'magnet_url': result.xpath('td/a')[0].attrib['href'],
                'detail_url': result.xpath('td/div[@class="detName"]/a')[0].attrib['href']
            }

            logger.debug(torrent)

            torrents.append(torrent)
    except IndexError:
        logger.exception('Error parsing search result.')

    return torrents


class PlaylistDownloader(threading.Thread):
    def __init__(self, session_manager):
        super(PlaylistDownloader, self).__init__()

        self.session_manager = session_manager

    def get_playlists(self, container):
        playlists = []
        for playlist in container:
            if playlist.type() == 'playlist':
                playlists.append(playlist)

        return playlists

    def get_tracks(self, playlists):
        tracks = set()

        for playlist in playlists:
            for track in playlist:
                tracks.add(track)

        return tracks

    def get_album_names(self, tracks):
        albums = set()

        for track in tracks:
            album = track.album()

            # Sometimes, queries fuck up. Maybe API throttling?
            assert album, 'No album. Try again.'
            album_name = u'%s %s' % (album.artist().name(), album.name())

            # Check if album is not in fact, empty (i.e. filled w spaces)
            if album_name.strip():
                logger.debug('Adding album %s', album_name)
                albums.add(album_name)

        return albums

    def get_torrents(self, album_name):
        """ Get torrents for album name. """
        logger.info('Searching for %s', album_name)

        torrents = pirate_search(album_name, category=101, sortorder=7)

        return torrents

    def run(self):
        container_loaded.wait()
        container_loaded.clear()

        # Get playlists
        playlists = self.get_playlists(self.session_manager.ctr)
        logger.info('Found %d playlists', len(playlists))

        # Get tracks
        tracks = self.get_tracks(playlists)
        logger.info('Found %d tracks', len(tracks))

        # Get albums
        album_names = self.get_album_names(tracks)
        logger.info('Found %d unique album names', len(album_names))

        # Disconnect
        self.session_manager.disconnect()

        # Save to file just to be sure
        # storefile = codecs.open('all_albums.txt', 'a', 'utf-8')
        # for album in album_names:
        #     storefile.write(u'%s\n' % album)
        # storefile.close()

        torrentfile = open('torrents.txt', 'a')
        rarefile = codecs.open('rare_albums.txt', 'a', 'utf-8')
        album_index = 1

        # Create list for indexing and sorting
        album_names = list(album_names)
        album_names.sort()

        # Take offset from command line
        album_names = album_names[self.session_manager.offset:]

        for album in album_names:
            # Make sure the user knows which album we're talking about
            print
            print '--', album, '(%d/%d)' % (album_index, len(album_names))
            album_index += 1

            torrents = self.get_torrents(album)

            # Yup. This needs refactoring.
            if torrents:
                if len(torrents) == 1:
                    # Only one torrent, select 1'st
                    torrent = torrents[0]

                    # Query whether or not to download
                    result = None
                    while not result in ('', 'y', 'n'):
                        result = raw_input('Download torrent? (y) ')
                        result = result.strip()

                    # No download, NEXT
                    if result == 'n':
                        logger.info('Skipping album.')
                        continue

                else:
                    # More than one, offer choice
                    assert len(torrents) > 1
                    print 'Multiple torrents found for \'%s\':' % album

                    index = 1
                    print 0, 'Skip this torrent'
                    for torrent in torrents:
                        print index, torrent['name'], torrent['detail_url']

                        index += 1
                    print -1, 'Exit'


                    result = None
                    while not isinstance(result, int):
                        result = raw_input("Which will it be? [1] ")

                        # Ugly validation
                        try:
                            result = int(result)

                            if result > len(torrents) or result < -1:
                                print 'Invalid value', result
                                result = None

                        except ValueError:

                            # Default to first option
                            if result.strip() == '':
                                result = 1

                    # Parse the result
                    if result == 0:
                        logger.info('Skipping album.')
                        continue

                    elif result == -1:
                        logger.info('Requested exit.')

                        # Close files
                        torrentfile.close()
                        rarefile.close()

                        # Bye-bye
                        return

                    torrent = torrents[result - 1]

            else:
                logger.info('Logging rare album.')

                rarefile.write(u'%s\n' % album)
                rarefile.flush()

                continue

            logger.info(
                'Found %s, writing magnet link to file.',
                torrent['name']
            )
            torrentfile.write('%s\n' % torrent['magnet_url'])

            # Flush to disk in case of interruption
            torrentfile.flush()

        torrentfile.close()
        rarefile.close()


class PlaylistManager(SpotifyPlaylistManager):
    def tracks_added(self, p, t, i, u):
        logger.debug('Tracks added to playlist %s', p.name())

    def tracks_moved(self, p, t, i, u):
        logger.debug('Tracks moved in playlist %s', p.name())

    def tracks_removed(self, p, t, u):
        logger.debug('Tracks removed from playlist %s', p.name())

    def playlist_renamed(self, p, u):
        logger.debug('Playlist renamed to %s', p.name())


class ContainerManager(SpotifyContainerManager):
    def container_loaded(self, c, u):
        logger.info('Fetching playlists')

        container_loaded.set()

    def playlist_added(self, c, p, i, u):
        logger.debug('Container: playlist "%s" added.', p.name())

    def playlist_moved(self, c, p, oi, ni, u):
        logger.debug('Container: playlist "%s" moved.', p.name())

    def playlist_removed(self, c, p, i, u):
        logger.debug('Container: playlist "%s" removed.', p.name())


class SessionManager(SpotifySessionManager):
    def __init__(self, *args, **kwargs):
        self.offset = kwargs.pop('offset', 0)

        super(SessionManager, self).__init__(*args, **kwargs)
        self.container_manager = ContainerManager()
        self.playlist_manager = PlaylistManager()

        self.playlist_downloader = PlaylistDownloader(self)

    def logged_in(self, session, error):
        if error:
            logger.error(error)
            return

        logger.info('Logged in as: %s', self.session.display_name())

        self.ctr = session.playlist_container()
        self.container_manager.watch(self.ctr)

        if not self.playlist_downloader.is_alive():
            logger.info('Starting playlist downloader.')
            self.playlist_downloader.start()


def main(argv=None):
    parser = argparse.ArgumentParser(description=
        'Search for and download all of your Spotify playlists from The Pirate Bay.'
    )

    parser.add_argument('username', type=str)
    parser.add_argument('password', type=str, nargs='?')
    parser.add_argument('--logging', '-l', help='Log level.', type=str, default='info', choices=('debug', 'info', 'warn', 'error'))
    parser.add_argument('--offset', type=int)

    args = parser.parse_args()

    # Setup logging
    console = logging.StreamHandler()
    logger.addHandler(console)

    numeric_level = getattr(logging, args.logging.upper())
    logger.setLevel(numeric_level)


    # Make sure we have a password
    if args.password:
        password = args.password
    else:
        print 'Please enter your Spotify password below.'
        password = getpass.getpass()

    session_m = SessionManager(args.username, password, True, offset=args.offset)
    session_m.connect()


if __name__ == "__main__":
    sys.exit(main())
