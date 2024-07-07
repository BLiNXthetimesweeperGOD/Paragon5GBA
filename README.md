# About
A repository for reverse engineering and documenting the Paragon 5/GBASS sound driver

Several games used this driver. A few games worth noting:
- Godzilla: Domination!
- Shantae Advance (prototype/demo version, used Godzilla BGM as placeholders)
- Hardcore Pinball


# Known/partially documented features
- Songs have internal names (no need to guess what they're called!)
- Has a super easy to scan for byte string that shows up right before the song table (00 00 00 00 01 01 00 00 02 00 00 00)
- Each channel is assigned an instrument alongside the pointer to the sequence table for the said channel
- Each channel of a song is stored as several sub-sequences with a timer between each one (if a sequence is corrupted, the next one will always eventually start playing)
- Notes have a variable before them that determines the base pitch. All note values are in a range between 0x20 and 0x2C.
- Note off events always start with a value between 0x30 and 0x4F followed up by the note length (the value before the length can act as a multiplier of sorts)

