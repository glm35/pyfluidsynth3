#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Show how to use a FluidSynth object.

Create and configure a synth, then play a crazy note sequence.

Run with:

  $ cd /path/to/pyfluidsynth3
  $ PYTHONPATH=. python3 examples/synth.py

Based on the examples from pyfluidsynth by MostAwesomeDude.
"""

import argparse
import pathlib
import sys
import time
from typing import Optional

from pyfluidsynth3 import fluidaudiodriver, fluidhandle, fluidsettings, fluidsynth


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-sf", "--soundfont",
                        help="Path to the sound font .sf2 file "
                             "(optional, synth.py will try to find it).")
    parser.add_argument("-l", "--fluidsynth-library",
                        help="Path to libfluidsynth (optional, pyfluidsynth3 will try to find it).")
    parser.add_argument("-ad", "--audio-driver", default='alsa',
                        help="Audio driver to be used by fluidsynth (default: alsa)")
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


class Synth:
    def __init__(self, soundfont, fluidsynth_library, audio_driver):
        """Create and configure a FluidSynth object."""
        self.handle = fluidhandle.FluidHandle(fluidsynth_library)
        self.settings = fluidsettings.FluidSettings(self.handle)
        self.synth = fluidsynth.FluidSynth(self.handle, self.settings)
        self.settings['audio.driver'] = audio_driver
        self.driver = fluidaudiodriver.FluidAudioDriver(self.handle, self.synth, self.settings)

        self.synth.load_soundfont(str(soundfont))

    def __del__(self):
        """Delete a FluidSynth object.

        This is needed to avoid a core dump at the end of the program.
        """
        del self.driver
        del self.synth

    def play_sequence(self):
        """Play a crazy sequence of notes."""
        seq = (79, 78, 79, 74, 79, 69, 79, 67, 79, 72, 79, 76,
               79, 78, 79, 74, 79, 69, 79, 67, 79, 72, 79, 76,
               79, 78, 79, 74, 79, 72, 79, 76, 79, 78, 79, 74,
               79, 72, 79, 76, 79, 78, 79, 74, 79, 72, 79, 76,
               79, 76, 74, 71, 69, 67, 69, 67, 64, 67, 64, 62,
               64, 62, 59, 62, 59, 57, 64, 62, 59, 62, 59, 57,
               64, 62, 59, 62, 59, 57, 43)

        for note in seq:
            self.synth.noteon(0, note, 1.0)
            time.sleep(0.1)
            self.synth.noteoff(0, note)


if __name__ == "__main__":
    args = parse_args()

    soundfont = args.soundfont
    if soundfont is None:
        soundfont = find_soundfont()
        if soundfont is None:
            print('Error: no sound font can be found')
            sys.exit(1)
    print('Using sound font:', soundfont)

    synth = Synth(soundfont, args.fluidsynth_library, args.audio_driver)
    synth.play_sequence()
