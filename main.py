import copy
import random
import threading

import pygame

# --- LÓGICA DO PUZZLE ---
MOVS = ["cima", "baixo", "esquerda", "direita"]

def encontrar_zero(tab):
    for i in range(3):
        for j in range(3):
            if tab[i][j] == 0: return i, j

def mover(tab, movimento):
    i, j = encontrar_zero(tab)
    novo = copy.deepcopy(tab)
    if movimento == "cima" and i > 0: novo[i][j], novo[i-1][j] = novo[i-1][j], novo[i][j]
    elif movimento == "baixo" and i < 2: novo[i][j], novo[i+1][j] = novo[i+1][j], novo[i][j]
    elif movimento == "esquerda" and j > 0: novo[i][j], novo[i][j-1] = novo[i][j-1], novo[i][j]
    elif movimento == "direita" and j < 2: novo[i][j], novo[i][j+1] = novo[i][j+1], novo[i][j]
    return novo

def dist_manhattan(tab):
    pos_certa = {1:(0,0), 2:(0,1), 3:(0,2), 4:(1,0), 5:(1,1), 6:(1,2), 7:(2,0), 8:(2,1)}
    d = 0
    for i in range(3):
        for j in range(3):
            item = tab[i][j]
            if item != 0:
                x, y = pos_certa[item]
                d += abs(x-i) + abs(y-j)
    return d

# --- ALGORITMO GENÉTICO (COM FEEDBACK DE GERAÇÃO) ---
def genetico_thread(puzzle_inicial, info):
    tam_pop = 200
    geracoes = 2000
    pop = [[random.choice(MOVS) for _ in range(150)] for _ in range(tam_pop)]
    
    for g in range(geracoes):
        info['geracao'] = g  
        
        avaliados = []
        for ind in pop:
            tab = copy.deepcopy(puzzle_inicial)
            for m in ind:
                n = mover(tab, m)
                if n != tab: tab = n
            d = dist_manhattan(tab)
            avaliados.append((1/(1+d), d, ind))
        
        avaliados.sort(reverse=True, key=lambda x: x[0])
        melhor_da_vez = avaliados[0]
        info['melhor_dist'] = melhor_da_vez[1]

        if melhor_da_vez[1] == 0 or g == geracoes - 1:
            info['solucao'] = melhor_da_vez[2]
            info['pronto'] = True
            return

        nova_pop = []
        nova_pop.append(melhor_da_vez[2])
        
        while len(nova_pop) < tam_pop:
            p1 = max(random.sample(avaliados, 3), key=lambda x: x[0])[2]
            p2 = max(random.sample(avaliados, 3), key=lambda x: x[0])[2]
            corte = random.randint(1, len(p1)-2)
            filho = p1[:corte] + p2[corte:]
            if random.random() < 0.1: 
                filho[random.randint(0, len(filho)-1)] = random.choice(MOVS)
            nova_pop.append(filho)
        pop = nova_pop

# --- INTERFACE PYGAME ---
LARGURA, ALTURA = 450, 500 
TAM_CELULA = LARGURA // 3
COR_FUNDO = (25, 25, 25)
COR_PECA = (46, 204, 113) 
COR_VAZIO = (52, 73, 94)
COR_TEXTO = (255, 255, 255)
COR_IA = (241, 196, 15) 

def desenhar(tela, tab, fonte, status, info):
    tela.fill(COR_FUNDO)
    
    if status == "CALCULANDO":
    
        txt_carregando = fonte.render("IA EVOLUINDO...", True, COR_IA)
        tela.blit(txt_carregando, txt_carregando.get_rect(center=(LARGURA//2, ALTURA//2 - 20)))
        
        fonte_pequena = pygame.font.SysFont("Arial", 25, bold=True)
        txt_gen = fonte_pequena.render(f"Geração: {info['geracao']}", True, COR_TEXTO)
        txt_dist = fonte_pequena.render(f"Melhor Distância: {info['melhor_dist']}", True, COR_TEXTO)
        
        tela.blit(txt_gen, txt_gen.get_rect(center=(LARGURA//2, ALTURA//2 + 30)))
        tela.blit(txt_dist, txt_dist.get_rect(center=(LARGURA//2, ALTURA//2 + 65)))
        
    else:
    
        for i in range(3):
            for j in range(3):
                valor = tab[i][j]
                rect = pygame.Rect(j*TAM_CELULA+5, i*TAM_CELULA+5, TAM_CELULA-10, TAM_CELULA-10)
                pygame.draw.rect(tela, COR_PECA if valor != 0 else COR_VAZIO, rect, border_radius=10)
                if valor != 0:
                    txt = fonte.render(str(valor), True, COR_TEXTO)
                    tela.blit(txt, txt.get_rect(center=rect.center))
        
        # Rodapé com info final
        fonte_pequena = pygame.font.SysFont("Arial", 15)
        txt_fim = fonte_pequena.render("Solução encontrada pelo Algoritmo Genético!", True, COR_IA)
        tela.blit(txt_fim, txt_fim.get_rect(center=(LARGURA//2, ALTURA - 30)))
    
    pygame.display.flip()

def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("8-Puzzle")
    fonte = pygame.font.SysFont("Arial", 50, bold=True)
    
    puzzle_inicial = [[1, 4, 2], [3, 5, 0], [6, 7, 8]]
    tab_atual = copy.deepcopy(puzzle_inicial)
    
    info = {
        'pronto': False, 
        'solucao': [], 
        'geracao': 0, 
        'melhor_dist': 0
    }
    
    thread_ia = threading.Thread(target=genetico_thread, args=(puzzle_inicial, info))
    thread_ia.daemon = True 
    thread_ia.start()
    
    status = "CALCULANDO"
    indice_mov = 0
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        if status == "CALCULANDO" and info['pronto']:
            status = "ANIMANDO"
            movimentos = info['solucao']

        if status == "ANIMANDO" and indice_mov < len(movimentos):
            pygame.time.wait(200)
            proximo = mover(tab_atual, movimentos[indice_mov])
            if proximo != tab_atual: 
                tab_atual = proximo
            indice_mov += 1

        desenhar(tela, tab_atual, fonte, status, info)
        clock.tick(60)

if __name__ == "__main__":
    main()