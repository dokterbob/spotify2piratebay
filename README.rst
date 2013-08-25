spotify2piratebay
=================

Search for and download all of your Spotify playlists from The Pirate Bay.
--------------------------------------------------------------------------

**Artists and other copyright holders who feel left out: you should have and
should allow your fans to give you money. Straight away. No record companies,
no DRM, no hassles. If you want to discuss about a sensible replacement for
copyright, you are welcome. But first make sure we can directly give you
money rather than having to pay some of the terrorists in the music industry.**

**To Spotify: make your client as fast as my local server, again. Make sure
the iOS and Android clients run as smoothly as the Symbian client. Remove the
Facebook requirement. Communicate how large a cut actually gets to the artists.
You have had, in the past, a sublime product and actually got me to pay for
music. Your service level has declined. The application is as large and lump
as iTunes right now. Sorry.**

**NOTE: You need to be a premium user to use this service.**

Usage.
------

1. Download and install `libspotify <https://developer.spotify.com/technologies/libspotify/>`_. On a Mac with homebrew, simply run::

       brew install libspotify

2. Install `spotify2piratebay`::

       pip install git+https://github.com/dokterbob/spotify2piratebay.git#egg=spotify2piratebay

3. Install a Spotify API key in the `spotify2piratebay` folder. Request one
   from Spotify. Alternately, using `Google <https://www.google.nl/search?q=inurl:spotify_appkey.key>`_ a key is easily found. Find where to
   install the key file with the following command::

       python -c 'import spotify2piratebay; print spotify2piratebay.__path__[0]'

4. Run the darn program::

       spotify2piratebay <username>

TODO
----
MUCH! This was more like a dirty hack than anything else. Pull req's welcome.
