"""Simple UI overlay for the simulation."""

import pygame
from typing import List, Optional
from .celestial_body import CelestialBody
from .physics import PhysicsEngine


class UI:
    """
    Simple UI overlay for displaying simulation information.
    Uses Pygame for 2D text rendering over the 3D scene.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize the UI.
        
        Args:
            width: Window width
            height: Window height
        """
        self.width = width
        self.height = height
        
        # Initialize fonts
        pygame.font.init()
        self.font_large = pygame.font.SysFont('Arial', 24)
        self.font_medium = pygame.font.SysFont('Arial', 18)
        self.font_small = pygame.font.SysFont('Arial', 14)
        
        # Colors
        self.text_color = (255, 255, 255)
        self.highlight_color = (255, 255, 0)
        self.dim_color = (150, 150, 150)
        
        # Show help overlay
        self.show_help = False
        self.show_info = True
    
    def resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        self.width = width
        self.height = height
    
    def render(self, screen: pygame.Surface, physics: PhysicsEngine, 
               fps: float, selected_body: Optional[CelestialBody] = None) -> None:
        """
        Render the UI overlay.
        
        Args:
            screen: Pygame surface to render to
            physics: Physics engine for simulation data
            fps: Current frames per second
            selected_body: Currently selected celestial body
        """
        if self.show_help:
            self._render_help(screen)
        
        if self.show_info:
            self._render_info(screen, physics, fps)
        
        if selected_body:
            self._render_body_info(screen, selected_body)
        
        # Always show minimal controls hint
        self._render_controls_hint(screen, physics)
    
    def _render_text(self, screen: pygame.Surface, text: str, x: int, y: int,
                     font: pygame.font.Font = None, color: tuple = None) -> int:
        """
        Render text to the screen.
        
        Returns:
            The y position for the next line
        """
        if font is None:
            font = self.font_medium
        if color is None:
            color = self.text_color
        
        surface = font.render(text, True, color)
        screen.blit(surface, (x, y))
        return y + font.get_height() + 2
    
    def _render_info(self, screen: pygame.Surface, physics: PhysicsEngine, fps: float) -> None:
        """Render simulation information."""
        x, y = 10, 10
        
        # Title
        y = self._render_text(screen, "Space Engine", x, y, self.font_large, self.highlight_color)
        y += 5
        
        # FPS
        y = self._render_text(screen, f"FPS: {fps:.1f}", x, y, self.font_small)
        
        # Time scale
        y = self._render_text(screen, f"Time Scale: {physics.time_scale:.1f}x", x, y, self.font_small)
        
        # Simulation status
        status = "PAUSED" if physics.paused else "RUNNING"
        status_color = (255, 100, 100) if physics.paused else (100, 255, 100)
        y = self._render_text(screen, f"Status: {status}", x, y, self.font_small, status_color)
        
        # Number of bodies
        y = self._render_text(screen, f"Bodies: {len(physics.bodies)}", x, y, self.font_small)
        
        # Total energy (for debugging/physics verification)
        if len(physics.bodies) > 0:
            energy = physics.total_energy()
            y = self._render_text(screen, f"Total Energy: {energy:.2e} J", x, y, self.font_small, self.dim_color)
    
    def _render_body_info(self, screen: pygame.Surface, body: CelestialBody) -> None:
        """Render information about a selected body."""
        x = 10
        y = self.height - 150
        
        y = self._render_text(screen, f"Selected: {body.name}", x, y, self.font_medium, self.highlight_color)
        y = self._render_text(screen, f"Mass: {body.mass:.2e} kg", x, y, self.font_small)
        y = self._render_text(screen, f"Radius: {body.radius:.1f}", x, y, self.font_small)
        y = self._render_text(screen, f"Position: ({body.position.x:.1f}, {body.position.y:.1f}, {body.position.z:.1f})", x, y, self.font_small)
        y = self._render_text(screen, f"Velocity: {body.velocity.magnitude:.2f} m/s", x, y, self.font_small)
        y = self._render_text(screen, f"Kinetic Energy: {body.kinetic_energy():.2e} J", x, y, self.font_small)
    
    def _render_controls_hint(self, screen: pygame.Surface, physics: PhysicsEngine) -> None:
        """Render a small controls hint at the bottom."""
        hint = "Press H for help | SPACE to pause | Mouse: rotate/zoom"
        surface = self.font_small.render(hint, True, self.dim_color)
        x = self.width - surface.get_width() - 10
        y = self.height - surface.get_height() - 10
        screen.blit(surface, (x, y))
    
    def _render_help(self, screen: pygame.Surface) -> None:
        """Render the help overlay."""
        # Semi-transparent background
        overlay = pygame.Surface((400, 400))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        
        x = (self.width - 400) // 2
        y = (self.height - 400) // 2
        screen.blit(overlay, (x, y))
        
        # Help content
        text_x = x + 20
        text_y = y + 20
        
        text_y = self._render_text(screen, "Controls", text_x, text_y, self.font_large, self.highlight_color)
        text_y += 10
        
        controls = [
            ("Mouse Drag", "Rotate camera"),
            ("Mouse Wheel", "Zoom in/out"),
            ("Middle Mouse Drag", "Pan camera"),
            ("SPACE", "Pause/Resume simulation"),
            ("+/-", "Adjust time scale"),
            ("R", "Reset camera"),
            ("C", "Clear all trails"),
            ("G", "Toggle grid"),
            ("T", "Toggle trails"),
            ("1", "Load Solar System"),
            ("2", "Load Binary Stars"),
            ("3", "Load Earth-Moon"),
            ("4", "Load Random System"),
            ("0", "Clear all bodies"),
            ("I", "Toggle info panel"),
            ("H", "Toggle this help"),
            ("ESC", "Quit"),
        ]
        
        for key, action in controls:
            key_surface = self.font_small.render(key, True, self.highlight_color)
            action_surface = self.font_small.render(f"  {action}", True, self.text_color)
            screen.blit(key_surface, (text_x, text_y))
            screen.blit(action_surface, (text_x + 120, text_y))
            text_y += 20
    
    def toggle_help(self) -> None:
        """Toggle the help overlay."""
        self.show_help = not self.show_help
    
    def toggle_info(self) -> None:
        """Toggle the info panel."""
        self.show_info = not self.show_info
