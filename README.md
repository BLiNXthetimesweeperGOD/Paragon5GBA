# About
A repository for reverse engineering and documenting the Paragon 5/GBASS sound driver

Several games used this driver. A few games worth noting:
- Godzilla: Domination!
- Shantae Advance (prototype/demo version, used Godzilla BGM as placeholders)
- Hardcore Pinball


# Known/partially documented features
- Songs have internal names (no need to guess what they're called!)
- Has a super easy to scan for byte string that shows up right before the song table (00 00 00 00 01 01 00 00 XX 00 00 00) (XX is the engine version number)
- Each channel is assigned an instrument alongside the pointer to the sequence table for the said channel
- Each channel of a song is stored as several sub-sequences with a timer between each one (if a sequence is corrupted, the next one will always eventually start playing)

# Currently known command list
- 0000 - End of sequence
- 0X, 00XX - Note off event for X amount of time
- 1X - Unknown
- 20-2C - Note (subtract 0x20 from it and add the note base pitch value * 0xC to it)
- 30-4F - Unknown
- 50-58 - Set note base pitch (subtract 0x50 from it for the value)
- 84, 85 - Pitch bends (how they work is unknown)

