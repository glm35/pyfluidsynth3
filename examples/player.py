#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Show how to use a FluidPlayer object to play a midi file.

Run with:

  $ cd /path/to/pyfluidsynth3
  $ PYTHONPATH=. python3 examples/player.py MIDI_FILE

Based on the examples from pyfluidsynth by MostAwesomeDude.
"""

import argparse
import pathlib
import sys
import time
from typing import Optional

from pyfluidsynth3 import fluidaudiodriver, fluidhandle, fluidsettings, fluidsynth
from pyfluidsynth3.fluidplayer import FluidPlayer


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Play a MIDI file")
    parser.add_argument("-sf", "--soundfont",
                        help="Path to the sound font .sf2 file "
                             "(optional, %(prog)s will try to find it).")
    parser.add_argument("-l", "--fluidsynth-library",
                        help="Path to libfluidsynth (optional, pyfluidsynth3 will try to find it).")
    parser.add_argument("-ad", "--audio-driver", default='alsa',
                        help="Audio driver to be used by fluidsynth (default: alsa)")
    parser.add_argument("midi_file", type=str,
                        help="Path to MIDI file")
    parser.add_argument("-r", "--repeat", type=int, default=1,
                        help="Number of times to repeat the playback (default: 1)")
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

        self.player = FluidPlayer(self.handle, self.synth)

    def __del__(self):
        del self.player
        del self.driver
        del self.synth

    def play_midi(self, midi_file: pathlib.Path, repeat: int = 1):
        print(f'Playing {midi_file}, repeat {repeat} time(s)')
        for _ in range(repeat):
            self.player.play(str(midi_file))
        while self.player.get_status() == FluidPlayer.PLAYING:
            time.sleep(1)
        # Remark: instead of polling player status, it is also possible to use
        # self.player.join().  But this is not interruptable with Ctrl+C.


if __name__ == "__main__":
    args = parse_args()

    soundfont = args.soundfont
    if soundfont is None:
        soundfont = find_soundfont()
        if soundfont is None:
            print('Error: no sound font can be found')
            sys.exit(1)
    print('Using sound font:', soundfont)
    print('Using audio driver:', args.audio_driver)

    player = Player(soundfont, args.fluidsynth_library, args.audio_driver)
    try:
        player.play_midi(args.midi_file, args.repeat)
    except KeyboardInterrupt:
        print('Playback aborted')
