import pygame

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

display_surface = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT)
)

pygame.display.set_caption(
    "Wildlife Information Display"
)

background_image = pygame.transform.scale(
    pygame.image.load("background.png").convert(),
    (SCREEN_WIDTH, SCREEN_HEIGHT)
)

wildlife_image = pygame.transform.scale(
    pygame.image.load("tiger.png").convert_alpha(),
    (200, 200)
)

wildlife_rect = wildlife_image.get_rect(
    center=(
        SCREEN_WIDTH // 2,
        SCREEN_HEIGHT // 2 - 50
    )
)

heading_font = pygame.font.Font(None, 42)
fact_font = pygame.font.Font(None, 24)

heading_text = heading_font.render(
    "Wildlife Spotlight: Tiger",
    True,
    pygame.Color("black")
)

heading_rect = heading_text.get_rect(
    center=(SCREEN_WIDTH // 2, 40)
)

fact_text = fact_font.render(
    "Tigers are powerful wild cats.",
    True,
    pygame.Color("black")
)

fact_rect = fact_text.get_rect(
    center=(SCREEN_WIDTH // 2, 420)
)

def game_loop():
    clock = pygame.time.Clock()

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        display_surface.blit(
            background_image,
            (0, 0)
        )

        display_surface.blit(
            wildlife_image,
            wildlife_rect
        )

        display_surface.blit(
            heading_text,
            heading_rect
        )

        display_surface.blit(
            fact_text,
            fact_rect
        )

        pygame.display.flip()

        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    game_loop()