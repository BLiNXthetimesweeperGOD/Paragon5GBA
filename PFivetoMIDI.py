import struct
import os
from tkinter import filedialog as fd
import mido
file = fd.askopenfilename()
base, ext = os.path.splitext(file)
outDir = base+"/"

if os.path.exists(outDir) == False:
    os.mkdir(outDir)

# Function to add MIDI messages to the track
def add_midi_message(message_type, channel, data1, data2, delta_time):
    if message_type == 'program_change':
        track.append(mido.Message('program_change', program=data1, channel=channel, time=delta_time))
    elif message_type == 'control_change':
        track.append(mido.Message('control_change', channel=channel, control=data1, value=data2, time=0))
    elif message_type == 'note_on':
        track.append(mido.Message('note_on', note=data1, velocity=data2, channel=channel, time=delta_time))
    elif message_type == 'note_off':
        track.append(mido.Message('note_off', note=data1, velocity=0, channel=channel, time=delta_time))
    elif message_type == 'pitch_wheel':
        track.append(mido.Message('pitchwheel', channel=channel, pitch=data1, time=delta_time))
        
with open(file, "rb") as f:
    f.seek(0xA0)
    ROMName = f.read(0xC).decode("UTF-8")
    ROMCode = f.read(0x4).decode("UTF-8")
    Count = 0

    #First check (most common, DAT3 is likely the version number for the engine)
    for i in range(int(os.path.getsize(file)/4)):
        DAT = f.read(4)
        if DAT == b'\x00\x00\x00\x00':
            DAT2 = f.read(4)
            if DAT2 == b'\x01\x01\x00\x00':
                DAT3 = f.read(4)
                if DAT3 == b'\x02\x00\x00\x00':
                    Count = struct.unpack("<I", f.read(4))[0]
                    Offset = struct.unpack("<I", f.read(4))[0]-0x08000000
                    print(ROMName,"("+ROMCode+")"+"\nSong count =",Count,"\nStart offset =",hex(Offset))
                    f.seek(Offset)
                    break
    
    if Count == 0: #Check 2
        f.seek(0)
        for i in range(int(os.path.getsize(file)/4)):
            DAT = f.read(4)
            if DAT == b'\x00\x00\x00\x00':
                DAT2 = f.read(4)
                if DAT2 == b'\x01\x01\x00\x00':
                    DAT3 = f.read(4)
                    if DAT3 == b'\x03\x00\x00\x00':
                        Count = struct.unpack("<I", f.read(4))[0]
                        Offset = struct.unpack("<I", f.read(4))[0]-0x08000000
                        print(ROMName,"("+ROMCode+")"+"\nSong count =",Count,"\nStart offset =",hex(Offset))
                        f.seek(Offset)
                        break
                    
    if Count == 0: #Check 3
        f.seek(0)
        for i in range(int(os.path.getsize(file)/4)):
            DAT = f.read(4)
            if DAT == b'\x00\x00\x00\x00':
                DAT2 = f.read(4)
                if DAT2 == b'\x01\x01\x00\x00':
                    DAT3 = f.read(4)
                    if DAT3 == b'\x04\x00\x00\x00':
                        Count = struct.unpack("<I", f.read(4))[0]
                        Offset = struct.unpack("<I", f.read(4))[0]-0x08000000
                        print(ROMName,"("+ROMCode+")"+"\nSong count =",Count,"\nStart offset =",hex(Offset))
                        f.seek(Offset)
                        break

    for i in range(Count):
        Name = ""
        A = 1
        TCount = struct.unpack("<I", f.read(4))[0]
        TPTROffset = struct.unpack("<I", f.read(4))[0]-0x08000000
        TNameOffset = struct.unpack("<I", f.read(4))[0]-0x08000000
        last = f.tell()
        f.seek(TNameOffset)
        while A != 0:
            A = f.read(1)[0]
            Letter = chr(A)
            Name = Name+Letter
        trackID = 0
        f.seek(TPTROffset)
        #print("_______________________________________________________")
        #print("Song name =",Name)
        for i in range(TCount):
            mid = mido.MidiFile(type=1)
            track = mido.MidiTrack()
            mid.tracks.append(track)
            track.append(mido.MetaMessage('set_tempo', tempo=5000000))
            TOffset = struct.unpack("<I", f.read(4))[0]-0x08000000
            TInstrumentID = f.read(4)[0]#struct.unpack("<I", f.read(4))[0]
            add_midi_message('program_change', 0, TInstrumentID, None, 0)
            
            prevTrack = f.tell()
            f.seek(TOffset)
            check = 0x10
            
            lastNote = 0
            
            
            try:
                while check == 0x10:
                    
                    dCheck = 0
                    check = f.read(1)[0]
                    SEQOffset = struct.unpack("<I", f.read(4))[0]-0x08000000
                    #print(f"{Name} {hex(SEQOffset)} {trackID} {hex(f.tell())}")
                    #input()
                    SEQDur1 = struct.unpack(">BB", f.read(2))[1]
                    while dCheck != 0x10:
                        dCheck = f.read(1)[0]
                        if dCheck != 0x10:
                            f.seek(-1, 1)
                            SEQDur1 += struct.unpack(">BB", f.read(2))[1]
                            #print(SEQDur1)
                            #input()
                        #if dCheck == 0x10:
                    f.seek(-1, 1)
                    lastSEQ = f.tell()
                    f.seek(SEQOffset)
                    
                    ended = False
                    reads = 0
                    totalNoteLength = 0
                    while ended != True:
                        CMD1 = f.read(1)[0]
                        if totalNoteLength >= SEQDur1: #Forcefully end this if the data being parsed is irrelevant
                            break
                        if CMD1 == 0 and reads == 0:
                            add_midi_message('note_off', 0, 0, 127, SEQDur1)
                            ended = True
                            break
                        
                        elif CMD1 == 0 and reads > 0:
                            CMD2 = f.read(1)[0]
                            if CMD2 == 0:
                                endLength = SEQDur1-totalNoteLength
                                if endLength > 0:
                                    add_midi_message('note_off', 0, lastNote, 127, endLength)
                                ended = True
                                break
                            else:
                                add_midi_message('note_off', 0, lastNote, 127, CMD2)
                                totalNoteLength+=CMD2

                        if CMD1 in range(1, 0xF): #End of note and delay time
                            add_midi_message('note_off', 0, lastNote, 127, CMD1)
                            totalNoteLength+=CMD1
                                
                        if CMD1 in range(0x10, 0x1F):
                            "UNKNOWN!"
                            
                        if CMD1 in range(0x20, 0x2C):
                            note = (CMD1-0x20)+note_adder
                            ext = f.read(1)[0] #Every note is followed up by an unknown value
                            add_midi_message('note_on', 0, note, 127, 0) #Start the note
                            lastNote = note

                        if CMD1 == 0x43:
                            noteOffLength = f.read(1)[0]
                            if noteOffLength == 0:
                                print("Broke!")
                                input()
                                break
                            add_midi_message('note_off', 0, lastNote, 127, noteOffLength)
                            totalNoteLength+=noteOffLength
                            
                        if CMD1 in range(0x50, 0x58): #Set key range
                            note_adder = (CMD1-0x50)*0xC
                            note = f.read(1)[0]-0x20+note_adder
                            add_midi_message('note_on', 0, note, 127, 0) #Start the note
                            lastNote = note

                        if CMD1 == 0x84: #Start of pitch bend
                            data = f.read(3)
                            add_midi_message('note_off', 0, lastNote, 127, data[1])
                            add_midi_message('note_off', 0, lastNote, 127, data[2])

                        if CMD1 == 0x85: #End of pitch bend
                            endByte = f.read(1)
                            bendDuration = f.read(1)[0]
                            if bendDuration == 0:
                                bendDuration = f.read(1)[0]
                            add_midi_message('note_off', 0, lastNote, 127, bendDuration)
                            
                            
                        #if CMD1 in range(0x80, 0x8F): #Special events like pitch bends
                            #f.read(1)
                        reads+=1
                    f.seek(lastSEQ)
            except:
                "ERROR"
            base, ext = os.path.splitext(file)
            if Name[-1].encode('utf-8') == b'\x00':
                Name = Name[0:len(Name)-1]
            output_path = f"{outDir}{Name}_converted_{trackID}.mid"
            mid.save(output_path)
            #print(f"Conversion complete! MIDI file saved as {output_path}")
            
            trackID+=1
            f.seek(prevTrack)
            #print("\nTrack offset =",hex(TOffset),"\nInstrument ID =",hex(TInstrumentID))
        f.seek(last)


print("_______________________________________________________")
input("Press enter to close")
