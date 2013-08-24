#!/usr/bin/env python

import argparse, sys, logging, getpass

from spotify.manager import SpotifySessionManager


# Default logger
logger = logging.getLogger('spotify2piratebay')


class ListDownloader(SpotifySessionManager):
    def get_playlists(self):
        print self.session


    def logged_in(self, session, error):
        if error:
            logger.error(error)
            return

        logger.info('Logged in.')

        # Perform work
        playlists = self.get_playlists()

        # Disconnect
        self.disconnect()


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

    session_m = ListDownloader(args.username, password, True)
    session_m.connect()


if __name__ == "__main__":
    sys.exit(main())
