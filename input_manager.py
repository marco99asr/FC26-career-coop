# input_manager.py
import pygame
import ctypes
from ctypes import wintypes

class InputManager:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.joysticks = []
        
        # Inizializza joystick
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            self.joysticks.append(joystick)
    
    def capture_controller_input(self, controller_id=0):
        """Cattura input da controller specifico"""
        if controller_id >= len(self.joysticks):
            return None
            
        pygame.event.pump()
        joystick = self.joysticks[controller_id]
        
        return {
            'left_x': joystick.get_axis(0),
            'left_y': joystick.get_axis(1),
            'right_x': joystick.get_axis(2),
            'right_y': joystick.get_axis(3),
            'l_trigger': (joystick.get_axis(4) + 1) / 2,
            'r_trigger': (joystick.get_axis(5) + 1) / 2,
            'a_button': joystick.get_button(0),
            'b_button': joystick.get_button(1),
            'x_button': joystick.get_button(2),
            'y_button': joystick.get_button(3),
            'l_bumper': joystick.get_button(4),
            'r_bumper': joystick.get_button(5)
        }