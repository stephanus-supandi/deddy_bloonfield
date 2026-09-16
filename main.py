"""DEADLY KUPERFIELD — entry point. Run: python main.py"""

import sys
import pygame
from config import SCREEN_W, SCREEN_H, FPS
from game import Game

def main():
    # initialize audio BEFORE display so the procedural SoundManager works.
    # Failure here is fine — the game is fully playable without audio.
    try:
        pygame.mixer.pre_init(22050, -16, 1, 512)
    except Exception:
        pass

    try:
        pygame.init()
    except Exception as exc:
        print(f"pygame failed to initialize: {exc}")
        sys.exit(1)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("DEADLY KUPERFIELD")

    Game(screen).run()

if __name__ == "__main__":
    main()