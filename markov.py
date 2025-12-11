import os
import mido
import numpy as np
import random
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from collections import Counter

# LEITURA E MODELAGEM

def ler_midi(arquivo_midi):
    mid = mido.MidiFile(arquivo_midi)
    dados = []
    
    ticks_por_batida = mid.ticks_per_beat
    
    tempo_original = 500000 
    instrumento_original = 0 
    
    for msg in mid:
        if msg.type == 'set_tempo':
            tempo_original = msg.tempo
        if msg.type == 'program_change':
            instrumento_original = msg.program

    for msg in mid:
        if not msg.is_meta and msg.type == 'note_on' and msg.velocity > 0:
            # tupla: (nota, tempo, velocity)
            dados.append((msg.note, msg.time, msg.velocity))
            
    return dados, tempo_original, ticks_por_batida, instrumento_original

def treinar_markov_2_ordem(dados):
    # Treina a cadeia de segunda ordem para geração da melodia
    cadeia = {}
    if len(dados) < 3: return None

    for i in range(len(dados) - 2):
        nota_passada = dados[i][0]
        nota_atual = dados[i+1][0]
        evento_futuro = dados[i+2] 
        
        chave = (nota_passada, nota_atual)
        if chave not in cadeia:
            cadeia[chave] = []
        cadeia[chave].append(evento_futuro)
    return cadeia

# VISUALIZAÇÃO E ANÁLISE

def midi_to_nota(note_number):
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return notes[note_number % 12] # ignorando oitavas

def gerar_visualizacoes(dados):
    print("\nGerando Visualizações:")
    
    notas_raw = [d[0] for d in dados] # notas em sequência da música 
    notas_classes = [midi_to_nota(n) for n in notas_raw] # notas da música inteira em notação 'C', 'C#', 'D' etc
    
    ordem_cromatica = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    nota_para_idx = {nome: i for i, nome in enumerate(ordem_cromatica)} # atribuindo índices {'C': 0, 'C#': 1, 'D': 2, ...}
    
    n = 12 
    P = np.zeros((n, n)) # matriz P (12x12)
    
    # iterando por cada nota da música em sequência
    for i in range(len(notas_classes) - 1):
        idx_origem = nota_para_idx[notas_classes[i]] # índice da nota de origem
        idx_destino = nota_para_idx[notas_classes[i+1]] # índice da nota de destino
        P[idx_destino, idx_origem] += 1 # somamos 1 naquele índice (destino x origem)
        
    # normalizando
    for j in range(n):
        soma = np.sum(P[:, j]) # soma os elementos da coluna
        if soma > 0:
            P[:, j] /= soma # transformando em porcentagem
        else:
            P[:, j] = 1.0 / n # se nenhuma nota seguir aquela, distribui igualmente a probabilidade

    # HEATMAP
    plt.figure(figsize=(10, 8))
    sns.heatmap(P, xticklabels=ordem_cromatica, yticklabels=ordem_cromatica, 
                cmap="Blues", linewidths=1, linecolor='gray', annot=True, fmt=".2f")
    plt.title("Matriz de Transição Harmônica (Probabilidades)")
    plt.xlabel("Nota Atual (j)")
    plt.ylabel("Próxima Nota (i)")
    plt.tight_layout()
    plt.savefig(f"output/heatmap_{nome_arquivo}.png")

    # GRAFO
    G = nx.DiGraph()
    notas_presentes = set(notas_classes) # apenas as notas que aparecem na música
    for nota in notas_presentes:
        G.add_node(nota)
    
    edge_labels = {}
    
    # limpando as probabilidades não expressivas
    limiar_visual = 0.20 
    
    for i in range(n): # destino
        for j in range(n): # origem
            peso = P[i, j]
            if peso > limiar_visual and ordem_cromatica[j] in notas_presentes:
                origem = ordem_cromatica[j]
                destino = ordem_cromatica[i]
                
                # adiciona aresta
                G.add_edge(origem, destino, weight=peso)
                
                # guarda a probabildiade formatada
                edge_labels[(origem, destino)] = f"{peso:.2f}"

    plt.figure(figsize=(12, 12))
    pos = nx.circular_layout(G) 
    
    # desenhando os nós
    nx.draw_networkx_nodes(G, pos, node_size=1500, node_color='white', edgecolors='black', linewidths=2)
    nx.draw_networkx_labels(G, pos, font_size=14, font_weight='bold', font_family='sans-serif')
    
    # espessura e cor
    edges = G.edges()
    weights = [G[u][v]['weight'] for u, v in edges]
    
    widths = [w * 8 + 1.0 for w in weights]
    
    edge_colors = weights
    
    nx.draw_networkx_edges(G, pos, width=widths, arrowstyle='-|>', 
                         arrowsize=30, 
                         edge_color=edge_colors, 
                         edge_cmap=plt.cm.Reds, 
                         edge_vmin=0, edge_vmax=1,
                         connectionstyle='arc3,rad=0.15')
    
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                               label_pos=0.3, font_size=10, 
                               bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    
    plt.title(f"Grafo de Harmonia (Transições > {limiar_visual*100}%)", fontsize=16)
    plt.axis('off')
    plt.savefig(f"output/grafo_{nome_arquivo}.png")

    # NOTA DOMINANTE 
    # método da potência
    v = np.ones(n) / n # chute inicial
    for _ in range(200):
        v = P @ v
        v = v / np.linalg.norm(v) # normalizando para evitar overflow

    # transformando em porcentagem
    v_prob = v / np.sum(v)
    
    plt.figure(figsize=(12, 6))
    colors = ['#d62728' if p > 0.1 else '#aaaaaa' for p in v_prob] 
    plt.bar(ordem_cromatica, v_prob, color=colors)
    plt.title("Nota Dominante (Autovetor Dominante)", fontsize=14)
    plt.xlabel("Notas", fontsize=12)
    plt.ylabel("Probabilidade Estacionária", fontsize=12)
    plt.tight_layout()
    plt.savefig(f"output/dominante_{nome_arquivo}.png")


# GERAÇÃO E SALVAMENTO

def gerar_musica(cadeia, semente_inicial, tamanho=200):
    musica_gerada = list(semente_inicial)
    nota_ant = semente_inicial[0][0]
    nota_atual = semente_inicial[1][0]
    
    for _ in range(tamanho):
        chave = (nota_ant, nota_atual)
        
        if chave in cadeia:
            possibilidades = cadeia[chave]
            proximo_evento = random.choice(possibilidades)
        else:
            nova_chave = random.choice(list(cadeia.keys()))
            proximo_evento = cadeia[nova_chave][0]

        musica_gerada.append(proximo_evento)
        nota_ant = nota_atual
        nota_atual = proximo_evento[0]
        
    return musica_gerada

def salvar_midi(dados, tempo_orig, ticks_orig, prog_orig, nome_arquivo="resultado.mid"):
    mid = mido.MidiFile(ticks_per_beat=ticks_orig) 
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    track.append(mido.MetaMessage('set_tempo', tempo=tempo_orig, time=0))
    track.append(mido.Message('program_change', program=prog_orig, time=0))
    
    fator_ajuste_tempo = 1.0 
    
    for nota, duracao, velocity_base in dados:
        variacao = random.randint(-5, 5)
        velocity_final = max(1, min(127, velocity_base + variacao))
        tempo_delta = int(duracao * fator_ajuste_tempo)
        
        track.append(mido.Message('note_on', note=nota, velocity=velocity_final, time=tempo_delta))
        duracao_nota = int(ticks_orig / 2) 
        track.append(mido.Message('note_off', note=nota, velocity=64, time=duracao_nota))
        
    mid.save(nome_arquivo)
    print(f"Salvo em {nome_arquivo}")

# BLOCO PRINCIPAL

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 teste.py input/arquivo.mid")
        sys.exit(1)

    caminho_entrada = sys.argv[1] 
    
    nome_arquivo = os.path.basename(caminho_entrada) 

    try:
        print(f"--- Processando: {nome_arquivo} ---")
        
        dados, bpm, ticks, instrumento = ler_midi(caminho_entrada)
        
        if len(dados) < 3:
            print("Erro: Arquivo insuficiente.")
        else:
            print("Gerando gráficos...")
            gerar_visualizacoes(dados) 
           
            print(f"Treinando Markov...")
            cerebro = treinar_markov_2_ordem(dados)
            
            print("Compondo...")
            semente = [dados[0], dados[1]]
            nova_musica = gerar_musica(cerebro, semente, tamanho=500)
            
            caminho_saida = f"output/remix_{nome_arquivo}"
            salvar_midi(nova_musica, bpm, ticks, instrumento, nome_arquivo=caminho_saida)
            
            print(f"\nSucesso! Confira a pasta 'output'.")

    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
