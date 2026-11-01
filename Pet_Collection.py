import pygame
import random
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
MOVEMENT_SPEED = 5
FONT_SIZE = 36
pygame.init()
background = pygame.image.load("pet_bg.png")
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
font = pygame.font.SysFont(None, FONT_SIZE)
class Sprite(pygame.sprite.Sprite):
    def __init__(self, color, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
    def update(self, x_change, y_change):
        self.rect.x += x_change
        self.rect.y += y_change
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pet Game")
all_sprites_list = pygame.sprite.Group()
pet = Sprite((255, 0, 0), 50, 50)
pet.rect.x = 50
pet.rect.y = 50
all_sprites_list.add(pet)
pet_food = Sprite((0, 255, 0), 20, 20)
pet_food.rect.x = random.randint(0, SCREEN_WIDTH - 20)
pet_food.rect.y = random.randint(0, SCREEN_HEIGHT - 20)
all_sprites_list.add(pet_food)
clock = pygame.time.Clock()
running = True
food_collected = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    keys = pygame.key.get_pressed()
    x_change = 0
    y_change = 0
    if keys[pygame.K_LEFT]:
        x_change = -MOVEMENT_SPEED
    if keys[pygame.K_RIGHT]:
        x_change = MOVEMENT_SPEED
    if keys[pygame.K_UP]:
        y_change = -MOVEMENT_SPEED
    if keys[pygame.K_DOWN]:
        y_change = MOVEMENT_SPEED
    pet.update(x_change, y_change)
    if pygame.sprite.collide_rect(pet, pet_food):
        all_sprites_list.remove(pet_food)
        food_collected = True
    screen.blit(background, (0, 0))
    all_sprites_list.draw(screen)
    if food_collected:
        win_text = font.render("Food collected!", True, (255, 255, 255))
        win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(win_text, win_rect)
    pygame.display.flip()
    clock.tick(60)
pygame.quit()