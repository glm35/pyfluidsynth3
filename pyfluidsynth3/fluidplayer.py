#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import ctypes

from . import constants, fluiderror, utility


class FluidPlayer:
    """ Represent the FluidSynth player object as defined in midi.h.

    This class is inspired by the FluidPlayer object from pyfluidsynth by MostAwesomeDude. Method
    documentation is mostly taken from FluidSynth's official API.

    Member:
    handle -- The handle to the FluidSynth library. Should be FluidHandle but a raw handle will
              probably work, too (FluidHandle).
    paused -- Indicates if the player is playing or inactive (boolean).
    player -- The FluidSynth player object (fluid_player_t).
    """

    def __init__(self, handle, synth):
        """ Create a new FluidSynth player instance using given handle and synth objects. """
        self.handle = handle
        self.player = self.handle.new_fluid_player(synth.synth)
        self.paused = True

    def __del__(self):
        """ Delete the player. """
        self.stop()
        self.join()

        if self.handle.delete_fluid_player(self.player) is constants.FAILED:
            raise fluiderror.FluidError("Couldn't delete fluid player!")

    def add(self, midi):
        """ Add a MIDI file to a player queue. """
        midi = utility.fluidstring(midi)
        self.handle.fluid_player_add(self.player, midi)

    def play(self, midi=None):
        """ Activate play mode for a MIDI player if not already playing. Also allows to add a MIDI
        file (see add()). """
        if midi:
            self.add(midi)
        self.handle.fluid_player_play(self.player)
        self.paused = False

    def seek(self, ticks: int):
        """ Seek in the currently playing file.

        Args:
            ticks: the position to seek to in the current file

        Returns:
            FLUID_FAILED if ticks is negative or after the latest tick of the file [or, since 2.1.3, if another seek
            operation is currently in progress], FLUID_OK otherwise.

            The actual seek will be performed when the synth calls back the player (i.e. a few levels above the
            player's callback set with fluid_player_set_playback_callback()). If the player's status is
            FLUID_PLAYER_PLAYING and a previous seek operation has not been completed yet, FLUID_FAILED is returned.
        """
        return self.handle.fluid_player_seek(self.player, ticks)

    def stop(self):
        """ Stop a MIDI player. """
        self.handle.fluid_player_stop(self.player)
        self.paused = True

    def get_total_ticks(self):
        """ Looks through all available MIDI tracks and gets the absolute tick of the very last event to play.

        Returns
            Total tick count of the sequence
        """
        return self.handle.fluid_player_get_total_ticks(self.player)

    def join(self):
        """ Wait for a MIDI player to terminate (when done playing). """
        self.handle.fluid_player_join(self.player)

    def set_loop(self, loop: int) -> None:
        """ Enable looping of a MIDI player.

        For example, if you want to loop the playlist twice, set loop to 2 and call this
        function before you start the player.

        Parameters:
            loop: Times left to loop the playlist. -1 means loop infinitely.
        """
        self.handle.fluid_player_set_loop(self.player, loop)

    def set_midi_tempo(self, tempo: int) -> None:
        """ Set the tempo of a MIDI player.

        Parameters:
            tempo: Tempo to set playback speed to (in microseconds per quarter note,
                   as per MIDI file spec)

        Note:
            Tempo change events contained in the MIDI file can override the specified tempo
            at any time!
        """
        self.handle.fluid_player_set_midi_tempo(self.player, tempo)

    def set_bpm(self, bpm: int) -> None:
        """ Set the tempo of a MIDI player in beats per minute.

        Parameters:
            bpm: Tempo in beats per minute

        Note:
            Tempo change events contained in the MIDI file can override the specified BPM
            at any time!
        """
        self.handle.fluid_player_set_bpm(self.player, bpm)

    def get_current_tick(self) -> int:
        """ Get the number of tempo ticks passed.

            Returns
                The number of tempo ticks passed
        """
        return self.handle.fluid_player_get_current_tick(self.player)

    # MIDI player tempo types:
    (TEMPO_DEFAULT, TEMPO_BPM, TEMPO_MIDI, TEMPO_RELATIVE) = range(0, 4)

    def set_tempo(self, tempo_type: int, tempo: float) -> None:
        """ Set MIDI player tempo: new API. """
        self.handle.fluid_player_set_tempo(self.player, tempo_type, tempo)

    # MIDI player status codes:
    (READY, PLAYING, DONE) = range(0, 3)

    def get_status(self) -> int:
        """ Get MIDI player status.

        Return player status:
            FluidPlayer.READY: Player is ready.
            FluidPlayer.PLAYING: Player is currently playing.
            FluidPlayer.DONE: Player is finished playing.
        """
        return self.handle.fluid_player_get_status(self.player)

    def get_bpm(self) -> int:
        """ Get the tempo of a MIDI player in beats per minute.

        Returns:
            MIDI player tempo in BPM
        """
        return self.handle.fluid_player_get_bpm(self.player)

    def get_midi_tempo(self) -> int:
        """ Get the tempo of a MIDI player.

        Returns:
            Tempo of the MIDI player (in microseconds per quarter note, as per MIDI file spec)
        """
        return self.handle.fluid_player_get_midi_tempo(self.player)

    def get_tempo(self, tempo_type: int = TEMPO_BPM) -> (int, int):
        """ Get the tempo of a MIDI player

        Args:
            tempo_type: one of TEMPO_DEFAULT, TEMPO_BPM, TEMPO_MIDI, TEMPO_RELATIVE

        Returns: a tuple (tempo, sync_mode)

        Raises: ValueError (incorrect parameter)
        """
        tempo = ctypes.c_double()
        sync_mode = ctypes.c_int()
        ret = self.handle.fluid_player_get_tempo(self.player, tempo_type,
                                                 ctypes.byref(tempo), ctypes.byref(sync_mode))
        if ret != constants.OK:
            raise ValueError

        if tempo_type in (self.TEMPO_DEFAULT, self.TEMPO_BPM, self.TEMPO_MIDI):
            tempo = int(tempo.value)
        sync_mode = int(sync_mode.value)

        return tempo, sync_mode

    def pause(self):
        """ Pause player or start again if already paused. """
        if self.paused:
            self.play()
        else:
            self.stop()
        self.paused = not self.paused
