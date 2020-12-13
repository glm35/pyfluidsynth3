#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Show how to use a FluidPlayer object to play one or more midi file(s)
and control their playback.

Run with:

  $ cd /path/to/pyfluidsynth3
  $ PYTHONPATH=. python3 examples/player_gui.py MIDI_FILES

"""

import argparse
import pathlib
import sys
import time
import tkinter as tk
from typing import List, Optional

from pyfluidsynth3 import fluidaudiodriver, fluidhandle, fluidsettings, fluidsynth
from pyfluidsynth3.fluidplayer import FluidPlayer


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Play MIDI file(s)")

    # Positional arguments
    parser.add_argument("midi_files", nargs='*', help="Path(s) to the MIDI file(s) to play")

    # Optional arguments
    parser.add_argument("-ad", "--audio-driver", default='alsa',
                        help="Audio driver to be used by fluidsynth (default: alsa)")
    parser.add_argument("-sf", "--soundfont",
                        help="Path to the sound font .sf2 file "
                             "(default: %(prog)s will try to find it).")
    parser.add_argument("-l", "--fluidsynth-library",
                        help="Path to libfluidsynth (default: pyfluidsynth3 will try to find it).")

    return parser.parse_args()


def find_soundfont() -> Optional[pathlib.Path]:
    """Try to find a soundfont"""

    # A few sound fonts from the fluid-soundfont-gm and timgm6mb-soundfont packages:
    soundfont_catalog = ['/usr/share/sounds/sf2/FluidR3_GM.sf2',
                         '/usr/share/sounds/sf2/TimGM6mb.sf2']
    for sf in soundfont_catalog:
        sf_path = pathlib.Path(sf)
        if sf_path.exists():
            return sf_path
    return None


class Player:
    def __init__(self, soundfont: Optional[pathlib.Path],
                 fluidsynth_library: Optional[str], audio_driver: str):
        self.handle = fluidhandle.FluidHandle(fluidsynth_library)
        self.settings = fluidsettings.FluidSettings(self.handle)

        self.synth = fluidsynth.FluidSynth(self.handle, self.settings)
        self.synth.load_soundfont(str(soundfont))

        self.settings['audio.driver'] = audio_driver
        self.driver = fluidaudiodriver.FluidAudioDriver(self.handle, self.synth, self.settings)

        self._fluidplayer = None

        self._playlist = []

    def __del__(self):
        if self._fluidplayer is not None:
            del self._fluidplayer
        del self.driver
        del self.synth

    # Playlist management

    def set_playlist(self, playlist):
        for midi_file in playlist:
            print("Player: set_playlist: add midi file:", midi_file)
            self._playlist.append(midi_file)

    def get_playlist(self):
        return list(self._playlist)

    # Playback control

    def play(self):
        """Start playing tunes in the playlist."""
        print("Player: play")

        if self._fluidplayer is None:
            self._fluidplayer = FluidPlayer(self.handle, self.synth)
            for midi_file in self._playlist:
                self._fluidplayer.add(midi_file)
        else:
            self._fluidplayer.play()

    def pause(self):
        """Pause playback."""
        print("Player: pause")
        if self._fluidplayer is not None:
            self._fluidplayer.stop()  # fluid_player_stop() actually just pauses playback...

    def stop(self):
        """Stop playing."""
        print("Player: stop")
        if self._fluidplayer is not None:
            # No way to stop playback and resume at the beginning of the
            # playlist with fluidsynth, so we just delete the player.
            # Before that we call stop(), else the last note will resonate for a while.
            # We need a short delay to let that happen before the player is
            # deleted.
            self._fluidplayer.stop()
            time.sleep(0.2)
            del self._fluidplayer
            self._fluidplayer = None


class PlayerGui:
    def __init__(self, player):
        self._player = player
        self._root = tk.Tk()
        self._root.title('pyfluidsynth3 example player GUI')

        self._playlist = tk.Listbox(self._root)
        self._playlist.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        for midi_file in self._player.get_playlist():
            self._playlist.insert(tk.END, midi_file)

        self._playback_control = tk.Frame(self._root)
        button_stop = tk.Button(self._playback_control, text='Stop',
                                command=self._player.stop)
        button_stop.pack(side=tk.LEFT)
        button_pause = tk.Button(self._playback_control, text='Pause',
                                 command=self._player.pause)
        button_pause.pack(side=tk.LEFT)
        button_play = tk.Button(self._playback_control, text='Play',
                                command=self._player.play)
        button_play.pack(side=tk.LEFT)
        self._playback_control.pack(fill=tk.X, expand=1)

    def mainloop(self):
        self._root.mainloop()


if __name__ == "__main__":
    args = parse_args()

    soundfont = args.soundfont
    if soundfont is None:
        soundfont = find_soundfont()
        if soundfont is None:
            print('Error: no sound font can be found')
            sys.exit(1)
    print('Using sound font:', soundfont)
    if args.fluidsynth_library:
        print('Using libfluidsynth:', args.fluidsynth_library)
    print('Using audio driver:', args.audio_driver)

    player = Player(soundfont, args.fluidsynth_library, args.audio_driver)
    player.set_playlist(args.midi_files)

    gui = PlayerGui(player)
    gui.mainloop()

