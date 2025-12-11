import mido
import sys
import os  

def processar_trilha_gerada(track, novo_canal, transpor_oitavas=1):
    novo_track = mido.MidiTrack()

    # transpondo oitava
    shift = transpor_oitavas * 12  
    
    for msg in track:
        nova_msg = msg.copy()
        
        if hasattr(nova_msg, 'channel'):
            nova_msg.channel = novo_canal
            
        if nova_msg.type in ['note_on', 'note_off']:
            # garantindo que, ao subir a oitava, ainda fique no limite MIDI (127)
            nova_nota = nova_msg.note + shift
            nova_msg.note = max(0, min(127, nova_nota))
            
        novo_track.append(nova_msg)
        
    return novo_track

def mixar_midis(arquivo_base, arquivo_melodia, arquivo_saida):
    try:
        mid_base = mido.MidiFile(arquivo_base)
        mid_melodia = mido.MidiFile(arquivo_melodia)
        
        mid_final = mido.MidiFile(type=1, ticks_per_beat=mid_base.ticks_per_beat)

        for track in mid_base.tracks:
            mid_final.tracks.append(track)
            
        CANAL_DESTINO = 2 
        OITAVAS_ACIMA = 1 
        
        for track in mid_melodia.tracks:
            if len(track) > 0:
                
                nova_trilha = processar_trilha_gerada(track, CANAL_DESTINO, OITAVAS_ACIMA)
                # nomeia a trilha para aparecer no player
                nova_trilha.insert(0, mido.MetaMessage('track_name', name='Melodia Markov'))
                
                mid_final.tracks.append(nova_trilha)

        mid_final.save(arquivo_saida)
        print(f"Salvo em: {arquivo_saida}")
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 mixar.py <original.mid> <gerado.mid>")
    else:
        arquivo_base = sys.argv[1]
        arquivo_gerado = sys.argv[2]
        nome_base = os.path.basename(arquivo_base)
        caminho_saida = f"output/mix_{nome_base}"
        
        mixar_midis(arquivo_base, arquivo_gerado, caminho_saida)