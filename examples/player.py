#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Show how to use a FluidPlayer object to play one or more midi file(s).

Run with:

  $ cd /path/to/pyfluidsynth3
  $ PYTHONPATH=. python3 examples/player.py MIDI_FILE

Based on the examples from pyfluidsynth by MostAwesomeDude.
"""

import argparse
import pathlib
import sys
import time
from typing import List, Optional

from pyfluidsynth3 import fluidaudiodriver, fluidhandle, fluidsettings, fluidsynth
from pyfluidsynth3.fluidplayer import FluidPlayer


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Play MIDI file(s)")

    # Positional arguments
    parser.add_argument("midi_files", nargs='*', help="Path(s) to the MIDI file(s) to play")

    # Optional arguments
    tempo_args = parser.add_mutually_exclusive_group()
    tempo_args.add_argument("--bpm", type=int, help="Tempo in beats per minute")
    tempo_args.add_argument("--midi-tempo", type=int, help="Tempo in microseconds per quarter note")
    parser.add_argument("-r", "--repeat", type=int, default=1,
                        help="Number of times to repeat the playback (default: 1). "
                             "-1 means repeat infinitely")
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

        self.player = FluidPlayer(self.handle, self.synth)

    def __del__(self):
        del self.player
        del self.driver
        del self.synth

    def set_tempo(self, bpm: Optional[int] = None, midi_tempo: Optional[int] = None):
        if bpm is not None:
            print(f'Set tempo (bpm): {bpm}')
            self.player.set_bpm(bpm)
        elif midi_tempo is not None:
            print(f'Set MIDI tempo (ms per quarter note): {midi_tempo}')
            self.player.set_midi_tempo(midi_tempo)
        else:
            pass

        # Remark: to convert from bpm to midi_tempo:
        # midi_tempo = int(60 * 1000 * 1000 / bpm)

    def get_tempo(self, tempo_type: str) -> int:
        """Get tempo

        Parameters:
            tempo_type: 'bpm' or 'midi_tempo'

        Returns:
            Player tempo for the requested tempo type
        """
        if tempo_type == 'midi_tempo':
            tempo = self.player.get_midi_tempo()
            print(f'Get MIDI tempo (ms per quarter note): {tempo}')
        else:
            tempo = self.player.get_bpm()
            print(f'Get tempo (bpm): {tempo}')
        return tempo

    def play_midi(self, midi_files: List[str], repeat: int = 1,
                  bpm: Optional[int] = None, midi_tempo: Optional[int] = None):
        print('Play MIDI file(s):', ', '.join(midi_files))
        if repeat != 1:
            if repeat == -1:
                print('Repeat forever')
            else:
                print(f'Repeat {repeat} times')

        self.get_tempo(tempo_type='midi_tempo' if midi_tempo is not None else 'bpm')

        for midi_file in midi_files:
            self.player.add(midi_file)

        if repeat != 1:
            self.player.set_loop(repeat)

        self.player.play()

        # Calling fluid_player_set_bpm() or fluid_player_set_midi_tempo() before fluid_player_play()
        # does not work, even if the midi file does not contain any tempo information.
        #
        # Workaround: set tempo a little while after playback start.  Besides the fragility of that
        # approach (the required delay may vary from machine to machine), there is another issue:
        # when a loop is set with fluid_player_set_loop(), the tempo is reset at the repeat.
        # Similarly, when two files without tempo set are added to the player queue with
        # fluid_player_add(), the tempo is reset when the second file starts playing.
        #
        # When no tempo is set in the midi file or via API: fluidsynth will play at bpm=120.

        time.sleep(0.01)
        self.set_tempo(bpm, midi_tempo)
        self.get_tempo(tempo_type='midi_tempo' if midi_tempo is not None else 'bpm')

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
        player.play_midi(args.midi_files, args.repeat, args.bpm, args.midi_tempo)
    except KeyboardInterrupt:
        print('Playback aborted')
