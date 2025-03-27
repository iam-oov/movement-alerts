import time
import pygame

pygame.mixer.init()
pygame.mixer.music.load("piano.wav")

while True:
    pygame.mixer.music.play()
    print("Playing piano")
    time.sleep(20)
