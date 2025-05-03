import struct
import os
import mido
from tkinter import filedialog as fd
from Library.codingTools import LE_BitReader, MidiFileHandler, fileTools

def parseSequenceData(rom, offsets, timings, instrument_id, output_path, song_name, track_id):
    """Parse sequence data and create a MIDI file"""
    midi = MidiFileHandler()
    midiFile, track = midi.create_midi_file()
    
    trackName = f"{song_name}_Track_{track_id}"
    midi.add_track_name(track, trackName)
    midi.add_tempo_change(track, midi.bpm_to_tempo(8))  #8 is about as close as we can get to the correct speed
    midi.set_pitch_bend_range(track, 2)  #Standard pitch bend range
    
    #Set the instrument
    track.append(midi.create_program_change_message(instrument_id))
    #print(offsets)
    basePitch = 3  #Starting octave
    lastNote = 0
    

    for i, offset in enumerate(offsets):
        rom.seek(offset)
        duration = 1
        end = False
        firstRead = True
        totalNoteLength = 0
        while not end:
            midi.add_lyrics(track, f'Offset: {hex(rom.tell()[0])}')
            cmd = rom.read(8)  #Read command byte
            #Command processing logic
            if cmd == 0:  #Rest or end
                if firstRead:
                    rom.read(8)
                else:
                    duration = rom.read(8)
                    if duration == 0:
                        endLength = timings[i] - totalNoteLength
                        if endLength > 0:
                            track.append(midi.create_note_off_message(lastNote, 0, time=endLength))
                        end = True
                    else:
                        track.append(midi.create_note_off_message(lastNote, 0, time=duration))
                        totalNoteLength += duration
            
            elif 1 <= cmd <= 0xF:  #End of note and delay time
                track.append(midi.create_note_off_message(lastNote, 0, time=cmd))
                totalNoteLength += cmd
                
            elif 0x20 <= cmd <= 0x2B:  #Note on
                note = (cmd - 0x20) + (basePitch * 12)
                ext = rom.read(8)  #Skip the unknown value
                if note < 128:  #Ensure note is in valid MIDI range
                    track.append(midi.create_note_on_message(note, 127, time=0))
                    lastNote = note
                   
            elif cmd == 0x43:  #Special note off
                duration = rom.read(8)
                if duration == 0:
                    break
                track.append(midi.create_note_off_message(lastNote, 0, time=duration))
                totalNoteLength += duration

            elif cmd == 0x4F:  #Unknown (might be read due to an error in handling another command)
                ""
                
            elif 0x50 <= cmd <= 0x58:  #Change base pitch
                basePitch = (cmd - 0x50)
                note = rom.read(8) - 0x20 + (basePitch * 12)
                if note < 128 and note > 0:
                    
                    track.append(midi.create_note_on_message(note, 127, time=0))
                    lastNote = note
                    
            elif cmd == 0x84:  #Start of pitch bend
                data = rom.read(8)#bytes([rom.read(8) for _ in range(3)])
                bendDuration = rom.read(8)
                if bendDuration == 0:
                    bendDuration = rom.read(8)
                track.append(midi.create_note_off_message(lastNote, 0, time=bendDuration))
                
            elif cmd == 0x85:  #End of pitch bend
                endByte = rom.read(8)
                bendDuration = rom.read(8)
                if bendDuration == 0:
                    bendDuration = rom.read(8)
                track.append(midi.create_note_off_message(lastNote, 0, time=bendDuration))
            #else:  #Unknown 
            #   input(f"UNKNOWN COMMAND {hex(cmd)} HIT AT {hex(rom.tell()[0])}")
                
            firstRead = False
            
    #Save the MIDI file
    midi.save_midi_file(midiFile, output_path)
    return output_path

def main():
    #Constants
    GBA_POINTER_BASE = 0x08000000  #Base offset for GBA ROM pointers
    
    #Engine version scan patterns
    ENGINE_SCANS = [
        b'\x00\x00\x00\x00\x01\x01\x00\x00\x02\x00\x00\x00',
        b'\x00\x00\x00\x00\x01\x01\x00\x00\x03\x00\x00\x00',
        b'\x00\x00\x00\x00\x01\x01\x00\x00\x04\x00\x00\x00'
    ]
    
    #Open file dialog for ROM selection
    filePath = fd.askopenfilename(title="Select GBA ROM file")
    if not filePath:
        print("No file selected. Exiting.")
        return
        
    #Create output directory
    base, ext = os.path.splitext(filePath)
    outDir = base + "/"
    workingDir = "working/"
    if not os.path.exists(outDir):
        os.mkdir(outDir)
    if not os.path.exists(workingDir):
        os.mkdir(workingDir)
    #Open the ROM file
    with open(filePath, "rb") as rom:
        romReader = LE_BitReader(rom)
        
        #Read ROM header info
        rom.seek(0xA0)
        romName = rom.read(0xC).decode("UTF-8", errors='ignore').strip('\x00')
        romCode = rom.read(0x4).decode("UTF-8", errors='ignore').strip('\x00')
        
        #Scan for engine signature
        engineFound = False
        for scan in ENGINE_SCANS:
            found, offset = fileTools.scanForBytes(filePath, scan)
            if found:
                engineFound = True
                engineOffset = offset
                break
                
        if not engineFound:
            print("Music engine signature not found in ROM. Exiting.")
            return
            
        #Go to song table
        rom.seek(engineOffset + 12)
        songCount = romReader.read(32)
        songTableOffset = romReader.read(32) - GBA_POINTER_BASE
        
        print(f"{romName} ({romCode})")
        print(f"Song count = {songCount}")
        print(f"Start offset = {hex(songTableOffset)}")
        validChecks = [2, 0x10]
        #Process each song
        rom.seek(songTableOffset)
        for songIndex in range(songCount):
            #Read song metadata
            trackCount = romReader.read(32)
            trackTableOffset = romReader.read(32) - GBA_POINTER_BASE
            trackNameOffset = romReader.read(32) - GBA_POINTER_BASE
            
            #Save current position
            nextSongPosition = rom.tell()
            
            #Get song name
            songName = fileTools.getZeroTerminatedString(filePath, trackNameOffset)
            if songName.endswith('\x00'):
                songName = songName[:-1]
            
            print(f"Processing song: {songName} - {trackCount} tracks offset = {hex(trackTableOffset)}")
            
            #Process each track in the song
            rom.seek(trackTableOffset)
            midis = []
            midi = MidiFileHandler()
            midiFile, track = midi.create_midi_file()
            for trackId in range(trackCount):
                #Read track data
                trackOffset = romReader.read(32) - GBA_POINTER_BASE
                instrumentId = romReader.read(8)  #Only read first byte for instrument ID
                rom.seek(rom.tell() + 3)  #Skip remaining bytes
                
                trackPosition = rom.tell()
                
                #Process sequences in the track
                rom.seek(trackOffset)
                offsets = []
                timings = []
                totalDuration = 0
                
                try:
                    while True:
                        check = romReader.read(8)
                        if check != 0x10:
                            break
                            
                        seqOffset = romReader.read(32) - GBA_POINTER_BASE
                        durationCheck = 0
                        seqDuration = 0
                        
                        while durationCheck == 0:
                            durationCheck = romReader.read(8)
                            if durationCheck == 0x2:
                                break
                            if durationCheck != 0x10:
                                seqDuration += romReader.read(8)
                            else:
                                rom.seek(-1, 1)
                            
                                
                        totalDuration += seqDuration
                        timings.append(seqDuration)
                        offsets.append(seqOffset)
                except Exception as e:
                    print(f"Error processing track {trackId}: {e}")
                    
                if offsets and timings:
                    outputPath = f"{workingDir}MIDI_Track_{trackId}.mid"
                    parsedFile = parseSequenceData(
                        romReader, offsets, timings, instrumentId, 
                        outputPath, songName, trackId
                    )
                rom.seek(trackPosition)
                midis.append(outputPath)
            midi.combine_midi_files(midis, f'{outDir}{songName}.mid')
            #Move to next song
            rom.seek(nextSongPosition)
    

if __name__ == "__main__":
    main()
