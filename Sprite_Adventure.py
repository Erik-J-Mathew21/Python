import pygame

def main():
    pygame.init()

    screen_width, screen_height = 500, 400
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Mini Sprite Adventure")

    x, y = 50, 50
    sprite_width, sprite_height = 60, 60
    speed = 4

    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    BLUE = (0, 125, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    YELLOW = (255, 255, 0)

    current_color = WHITE

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pressed = pygame.key.get_pressed()

        if pressed[pygame.K_LEFT]:
            x -= speed
        if pressed[pygame.K_RIGHT]:
            x += speed
        if pressed[pygame.K_UP]: