#!/usr/bin/env python

import argparse, sys, logging, getpass, threading, codecs

from spotify.manager import (
    SpotifySessionManager, SpotifyContainerManager, SpotifyPlaylistManager
)

import piratebay.internet, piratebay.constants


# Default logger
logger = logging.getLogger('spotify2piratebay')

# Threading humbug
container_loaded = threading.Event()

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
        page = piratebay.internet.search_main(
            term=album_name,
            category=piratebay.constants.categories["audio"]["music"]
        )

        torrents = set()
        for result in page.all():
            torrents.add({
                'name': result['name'],
                'info_url': result['torrent-info-url'],
                'magnet_url': result['magnet_url']
            })

        print torrents


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
        # storefile = codecs.open('albums.txt', 'w', 'utf-8')
        # for album in album_names:
        #     storefile.write(u'%s\n' % album)
        # storefile.close()

        for album in album_names:
            torrents = self.get_torrents(album)


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

    session_m = SessionManager(args.username, password, True)
    session_m.connect()

    print 'Disconnected'


if __name__ == "__main__":
    sys.exit(main())
