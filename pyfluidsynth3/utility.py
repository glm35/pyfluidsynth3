#! /usr/bin/env python3
# -*- coding: utf-8 -*-

def fluidstring(string):
    """ Converts a Python string to a FluidSynth compatible string. """
    return string.encode(encoding='utf-8')
