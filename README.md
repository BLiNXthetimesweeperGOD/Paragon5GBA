# About
A repository for reverse engineering and documenting the Paragon 5/GBASS sound driver

Feel free to reimplement, borrow or use this documentation for your own research and tools.

Several games used this driver. A few games worth noting:
- Godzilla: Domination!
- Shantae 2: Risky Revolution (Demo) (was recently released, reuses stuff from Godzilla)
- Hardcore Pinball


# Known/partially documented features
- Songs have internal names (no need to guess what they're called!)
- Has a super easy to scan for byte string that shows up right before the song table (00 00 00 00 01 01 00 00 XX 00 00 00) (XX is the engine version number)
- Each channel is assigned an instrument alongside the pointer to the sequence table for the said channel
- Each channel of a song is stored as several sub-sequences with a timer between each one (if a sequence is corrupted, the next one will always eventually start playing)
- Notes are played on a timer which appears to be done in frames. Each frame advanced on the GBA will generally decrease the timer value in RAM by 1. Lag will also generally slow the engine down.

# Currently known command list
- 0000 - End of sequence
- 0X, 00XX - Note off event for X amount of time
- 1X - Unknown
- 20-2C - Note (subtract 0x20 from it and add the note base pitch value * 0xC to it)
- 30-4F - Unknown
- 50-58 - Set note base pitch (subtract 0x50 from it for the value)
- 84, 85 - Pitch bends (how they work is unknown)

# Using PFivetoMIDI
Be sure that the Python mido library is installed and double click the script before navigating to your ROM.

Double click your ROM and the sequences should be converted to MIDI files in a folder named "/(ROM name)/" in the same folder as the ROM.

To-do list:
- Rewrite the entire script to use my Python BitReader class
- Document unknown commands
