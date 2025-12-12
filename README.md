# Gerando melodias aleatórias a partir de músicas aplicando conceitos de cadeias de Markov

```text
projeto/
├── input/
│   └── (coloque seus arquivos .mid originais aqui)
├── output/
│   ├── (aqui aparecerão os arquivos .mid gerados)
│   └── (aqui aparecerão os gráficos .png)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── markov.py
├── mixar.py
└── README.md
```

## 1. Iniciar Ambiente 
Abra o terminal na pasta do projeto e entre no modo interativo: 
```bash 
docker-compose run --rm app bash
```
## 2. Uso
Para gerar as visualizações e melodia:
```bash
python markov.py input/<sua_musica.mid>
```
Para juntar música original + melodia:
```bash
python mixar.py input/<sua_musica.mid> output/<remix_sua_musica.mid>
