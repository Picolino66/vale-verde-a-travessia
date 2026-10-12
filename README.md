# Vale Verde — A Travessia

Demo 2D de plataforma feito em Python com Pygame para a atividade de Linguagem de Programação Aplicada. O objetivo é atravessar a fase e alcançar a bandeira. Há abismos e inimigos; você tem três vidas. As cinco estrelas são opcionais e aparecem em desafios diferentes: degraus altos, sentinela no chão, ponte sobre a água, escalada e salto sobre o último inimigo. Os inimigos podem patrulhar, vigiar um ponto ou saltar.

## Controles

| Tecla | Ação |
| --- | --- |
| A / D ou ← / → | Mover |
| Espaço, W ou ↑ | Saltar |
| P | Pausar / continuar |
| Enter | Iniciar, continuar ou jogar novamente |
| Esc | Voltar ao menu; no menu, sair |

É possível derrotar inimigos saltando sobre eles. O menu do jogo também mostra os controles.

## Áudio

A música de `sounds/fundo-ambientacao.mp3` toca em loop e pausa junto com o jogo. Os demais arquivos da pasta `sounds/` são usados ao saltar, perder uma vida, derrotar um inimigo, coletar uma estrela e quando um inimigo entra na área visível. Mantenha `sounds/` ao lado de `main.py` ou, na versão compilada, ao lado de `ValeVerde.exe`.

## Executar pelo código

Instale Python 3.10 ou superior e execute na pasta do projeto:

```bash
python -m pip install -r requirements.txt
python main.py
```

Em distribuições Linux onde o comando é `python3`, use `python3` nos dois comandos.

## Gerar o ZIP para Windows

Em um computador Windows com Python instalado, abra a pasta do projeto no CMD e execute:

```bat
build_windows.bat
```

O script instala as dependências, compila `main.py` com PyInstaller, copia os assets usados e gera `dist\ValeVerde-Windows.zip`. Esse é o arquivo a entregar. Para testar, extraia o ZIP e execute `ValeVerde.exe`. As pastas `assets` e `sounds` devem continuar ao lado do executável.

## Organização dos assets

```text
assets/
├── characters/
│   ├── hero/           # ações idle, run, walk, jump e dead
│   └── enemies/        # male e female; cada um com walk, idle, attack e dead
├── tileset/
│   ├── background/     # fundo
│   ├── terrain/        # blocos de chão, plataformas e água
│   └── props/          # árvores, arbustos, cogumelos e placas
└── source/tileset/     # arquivos vetoriais originais; não entram no ZIP
```

O executável Windows precisa ser gerado no Windows; o PyInstaller não produz um `.exe` Windows a partir do Linux.
