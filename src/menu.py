"""Interactive menu UI for adding celestial bodies."""

import pygame
import math
from typing import List, Optional, Tuple, Callable
from .celestial_body import CelestialBody
from .vector3 import Vector3


class MenuItem:
    """Represents a draggable menu item."""
    
    def __init__(self, name: str, color: Tuple[float, float, float], 
                 mass: float, radius: float, is_star: bool = False):
        self.name = name
        self.color = color
        self.mass = mass
        self.radius = radius
        self.is_star = is_star
        self.rect = pygame.Rect(0, 0, 0, 0)
    
    def create_body(self, position: Vector3, velocity: Vector3) -> CelestialBody:
        """Create a celestial body from this menu item."""
        return CelestialBody(
            name=self.name,
            mass=self.mass,
            radius=self.radius,
            position=position,
            velocity=velocity,
            color=self.color,
            is_star=self.is_star
        )


class PresetItem:
    """Represents a preset solar system."""
    
    def __init__(self, name: str, description: str, loader: Callable):
        self.name = name
        self.description = description
        self.loader = loader
        self.rect = pygame.Rect(0, 0, 0, 0)


class Menu:
    """
    Sidebar menu for adding objects and loading presets.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize the menu.
        
        Args:
            width: Window width
            height: Window height
        """
        self.window_width = width
        self.window_height = height
        
        # Menu dimensions
        self.menu_width = 220
        self.collapsed = False
        self.toggle_rect = pygame.Rect(0, 0, 30, 80)
        
        # Initialize fonts
        pygame.font.init()
        self.font_title = pygame.font.SysFont('Arial', 18, bold=True)
        self.font_normal = pygame.font.SysFont('Arial', 14)
        self.font_small = pygame.font.SysFont('Arial', 12)
        
        # Colors
        self.bg_color = (20, 25, 35, 230)
        self.header_color = (40, 50, 70)
        self.item_color = (50, 60, 80)
        self.item_hover_color = (70, 85, 110)
        self.text_color = (220, 220, 220)
        self.accent_color = (100, 180, 255)
        
        # Dragging state
        self.dragging_item: Optional[MenuItem] = None
        self.drag_pos = (0, 0)
        
        # Scroll state
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Hover state
        self.hovered_item = None
        
        # Define celestial body templates with SCALED masses for visual physics
        # Stars: mass ~1000, Gas giants: ~10, Planets: ~1, Small bodies: ~0.01
        self.celestial_items: List[MenuItem] = [
            MenuItem("Sun", (1.0, 0.9, 0.0), 1000.0, 30, is_star=True),
            MenuItem("Red Dwarf", (1.0, 0.4, 0.2), 500.0, 15, is_star=True),
            MenuItem("Blue Giant", (0.6, 0.8, 1.0), 2000.0, 45, is_star=True),
            MenuItem("Mercury", (0.7, 0.7, 0.7), 0.06, 3),
            MenuItem("Venus", (0.9, 0.7, 0.5), 0.8, 5),
            MenuItem("Earth", (0.2, 0.5, 1.0), 1.0, 6),
            MenuItem("Mars", (0.8, 0.3, 0.1), 0.1, 4),
            MenuItem("Jupiter", (0.8, 0.7, 0.6), 10.0, 15),
            MenuItem("Saturn", (0.9, 0.8, 0.5), 5.0, 12),
            MenuItem("Uranus", (0.6, 0.8, 0.9), 3.0, 8),
            MenuItem("Neptune", (0.3, 0.4, 0.9), 3.0, 8),
            MenuItem("Moon", (0.7, 0.7, 0.7), 0.01, 4),
            MenuItem("Asteroid", (0.5, 0.5, 0.5), 0.001, 2),
            MenuItem("Comet", (0.8, 0.9, 1.0), 0.0001, 2),
        ]
        
        # Presets (will be populated by main app)
        self.preset_items: List[PresetItem] = []
        
        # Custom body editor
        self.show_custom_editor = False
        self.custom_name = "Custom Body"
        self.custom_mass = 5.0e24
        self.custom_radius = 6.0
        self.custom_color = (0.5, 0.8, 0.5)
        self.custom_is_star = False
        
        # Sections
        self.sections = ["Presets", "Stars", "Planets", "Small Bodies", "Custom"]
        self.section_expanded = {s: True for s in self.sections}
    
    def resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        self.window_width = width
        self.window_height = height
    
    def set_presets(self, presets: List[PresetItem]) -> None:
        """Set the available presets."""
        self.preset_items = presets
    
    def toggle_menu(self) -> None:
        """Toggle menu collapsed state."""
        self.collapsed = not self.collapsed
    
    def get_menu_rect(self) -> pygame.Rect:
        """Get the menu rectangle."""
        if self.collapsed:
            return pygame.Rect(self.window_width - 30, 0, 30, self.window_height)
        return pygame.Rect(self.window_width - self.menu_width, 0, 
                          self.menu_width, self.window_height)
    
    def point_in_menu(self, pos: Tuple[int, int]) -> bool:
        """Check if a point is inside the menu."""
        return self.get_menu_rect().collidepoint(pos)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[dict]:
        """
        Handle pygame events.
        
        Returns:
            Action dict if an action was triggered, None otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self._handle_click(event.pos)
            elif event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 30)
            elif event.button == 5:  # Scroll down
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 30)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_item:
                result = self._handle_drop(event.pos)
                self.dragging_item = None
                return result
        
        elif event.type == pygame.MOUSEMOTION:
            self.drag_pos = event.pos
            self._update_hover(event.pos)
        
        elif event.type == pygame.MOUSEWHEEL:
            if self.point_in_menu(pygame.mouse.get_pos()):
                self.scroll_offset = max(0, min(self.max_scroll, 
                                               self.scroll_offset - event.y * 30))
        
        return None
    
    def _handle_click(self, pos: Tuple[int, int]) -> Optional[dict]:
        """Handle mouse click."""
        menu_rect = self.get_menu_rect()
        
        # Check toggle button
        toggle_rect = pygame.Rect(menu_rect.x, menu_rect.centery - 40, 30, 80)
        if toggle_rect.collidepoint(pos):
            self.toggle_menu()
            return None
        
        if self.collapsed:
            return None
        
        if not menu_rect.collidepoint(pos):
            return None
        
        # Check presets
        for preset in self.preset_items:
            if preset.rect.collidepoint(pos):
                return {"action": "load_preset", "preset": preset}
        
        # Check celestial items (start drag)
        for item in self.celestial_items:
            if item.rect.collidepoint(pos):
                self.dragging_item = item
                return None
        
        # Check section headers
        # (Would toggle section expansion)
        
        return None
    
    def _handle_drop(self, pos: Tuple[int, int]) -> Optional[dict]:
        """Handle drop after dragging."""
        if not self.dragging_item:
            return None
        
        # Check if dropped outside menu
        if not self.point_in_menu(pos):
            return {
                "action": "add_body",
                "item": self.dragging_item,
                "screen_pos": pos
            }
        
        return None
    
    def _update_hover(self, pos: Tuple[int, int]) -> None:
        """Update hover state."""
        self.hovered_item = None
        
        if self.collapsed or not self.point_in_menu(pos):
            return
        
        for item in self.celestial_items:
            if item.rect.collidepoint(pos):
                self.hovered_item = item
                return
        
        for preset in self.preset_items:
            if preset.rect.collidepoint(pos):
                self.hovered_item = preset
                return
    
    def is_dragging(self) -> bool:
        """Check if currently dragging an item."""
        return self.dragging_item is not None
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the menu."""
        menu_rect = self.get_menu_rect()
        
        if self.collapsed:
            self._render_collapsed(screen, menu_rect)
        else:
            self._render_expanded(screen, menu_rect)
        
        # Render drag preview
        if self.dragging_item:
            self._render_drag_preview(screen)
    
    def _render_collapsed(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        """Render collapsed menu."""
        # Draw toggle button
        pygame.draw.rect(screen, self.header_color, rect)
        pygame.draw.rect(screen, self.accent_color, rect, 2)
        
        # Draw arrow
        arrow_text = "◀"
        text_surface = self.font_title.render(arrow_text, True, self.text_color)
        text_x = rect.x + (rect.width - text_surface.get_width()) // 2
        text_y = rect.centery - text_surface.get_height() // 2
        screen.blit(text_surface, (text_x, text_y))
    
    def _render_expanded(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        """Render expanded menu."""
        # Background
        bg_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        bg_surface.fill(self.bg_color)
        screen.blit(bg_surface, rect.topleft)
        
        # Border
        pygame.draw.rect(screen, self.accent_color, rect, 2)
        
        # Toggle button
        toggle_rect = pygame.Rect(rect.x, rect.centery - 40, 25, 80)
        pygame.draw.rect(screen, self.header_color, toggle_rect)
        arrow_text = "▶"
        text_surface = self.font_small.render(arrow_text, True, self.text_color)
        screen.blit(text_surface, (toggle_rect.x + 6, toggle_rect.centery - 6))
        
        # Content area
        content_x = rect.x + 30
        content_width = rect.width - 35
        y = rect.y + 10 - self.scroll_offset
        
        # Title
        title = self.font_title.render("SPACE ENGINE", True, self.accent_color)
        if y > 0:
            screen.blit(title, (content_x + (content_width - title.get_width()) // 2, y))
        y += 30
        
        # Presets section
        y = self._render_section(screen, "🌌 PRESETS", content_x, y, content_width)
        for preset in self.preset_items:
            if y > -40 and y < self.window_height:
                preset.rect = pygame.Rect(content_x, y, content_width, 35)
                is_hover = self.hovered_item == preset
                color = self.item_hover_color if is_hover else self.item_color
                pygame.draw.rect(screen, color, preset.rect, border_radius=5)
                pygame.draw.rect(screen, self.accent_color, preset.rect, 1, border_radius=5)
                
                name_text = self.font_normal.render(preset.name, True, self.text_color)
                screen.blit(name_text, (content_x + 10, y + 5))
                
                desc_text = self.font_small.render(preset.description, True, (150, 150, 150))
                screen.blit(desc_text, (content_x + 10, y + 20))
            else:
                preset.rect = pygame.Rect(0, 0, 0, 0)
            y += 40
        
        y += 10
        
        # Stars section
        y = self._render_section(screen, "⭐ STARS", content_x, y, content_width)
        for item in self.celestial_items:
            if item.is_star:
                y = self._render_item(screen, item, content_x, y, content_width)
        
        y += 10
        
        # Planets section
        y = self._render_section(screen, "🪐 PLANETS", content_x, y, content_width)
        planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
        for item in self.celestial_items:
            if item.name in planets:
                y = self._render_item(screen, item, content_x, y, content_width)
        
        y += 10
        
        # Small bodies section
        y = self._render_section(screen, "☄️ SMALL BODIES", content_x, y, content_width)
        small_bodies = ["Moon", "Asteroid", "Comet"]
        for item in self.celestial_items:
            if item.name in small_bodies:
                y = self._render_item(screen, item, content_x, y, content_width)
        
        y += 20
        
        # Instructions
        if y > 0 and y < self.window_height - 50:
            inst_text = self.font_small.render("Drag items to add to scene", True, (120, 120, 120))
            screen.blit(inst_text, (content_x + 10, y))
        
        # Update max scroll
        self.max_scroll = max(0, y + self.scroll_offset - self.window_height + 100)
    
    def _render_section(self, screen: pygame.Surface, title: str, 
                        x: int, y: int, width: int) -> int:
        """Render a section header."""
        if y > -30 and y < self.window_height:
            pygame.draw.line(screen, (60, 70, 90), (x, y + 8), (x + width, y + 8), 1)
            text = self.font_normal.render(title, True, self.accent_color)
            screen.blit(text, (x + 5, y))
        return y + 25
    
    def _render_item(self, screen: pygame.Surface, item: MenuItem,
                     x: int, y: int, width: int) -> int:
        """Render a celestial body item."""
        if y > -35 and y < self.window_height:
            item.rect = pygame.Rect(x, y, width, 30)
            
            is_hover = self.hovered_item == item
            is_dragging = self.dragging_item == item
            
            if is_dragging:
                color = self.accent_color
            elif is_hover:
                color = self.item_hover_color
            else:
                color = self.item_color
            
            pygame.draw.rect(screen, color, item.rect, border_radius=4)
            
            # Color preview circle
            circle_color = tuple(int(c * 255) for c in item.color)
            pygame.draw.circle(screen, circle_color, (x + 15, y + 15), 8)
            pygame.draw.circle(screen, (200, 200, 200), (x + 15, y + 15), 8, 1)
            
            # Name
            name_text = self.font_normal.render(item.name, True, self.text_color)
            screen.blit(name_text, (x + 30, y + 7))
            
            # Drag hint
            if is_hover and not is_dragging:
                hint = self.font_small.render("⋮⋮", True, (150, 150, 150))
                screen.blit(hint, (x + width - 20, y + 7))
        else:
            item.rect = pygame.Rect(0, 0, 0, 0)
        
        return y + 35
    
    def _render_drag_preview(self, screen: pygame.Surface) -> None:
        """Render the item being dragged."""
        if not self.dragging_item:
            return
        
        item = self.dragging_item
        x, y = self.drag_pos
        
        # Check if outside menu area - show placement indicator
        if not self.point_in_menu((x, y)):
            # Draw crosshair/reticle at drop location
            self._draw_placement_indicator(screen, x, y)
        
        # Semi-transparent preview following cursor
        preview_surface = pygame.Surface((120, 40), pygame.SRCALPHA)
        preview_surface.fill((50, 60, 80, 200))
        
        # Color circle
        circle_color = tuple(int(c * 255) for c in item.color)
        pygame.draw.circle(preview_surface, circle_color, (20, 20), 12)
        
        # Name
        name_text = self.font_normal.render(item.name, True, self.text_color)
        preview_surface.blit(name_text, (40, 12))
        
        # Draw centered on cursor
        screen.blit(preview_surface, (x - 60, y - 20))
    
    def _draw_placement_indicator(self, screen: pygame.Surface, x: int, y: int) -> None:
        """Draw a visual indicator showing where the object will be placed."""
        # Outer circle (pulsing effect based on time)
        import time
        pulse = abs(math.sin(time.time() * 4)) * 0.3 + 0.7
        outer_radius = int(30 * pulse)
        
        # Draw concentric circles
        for i, radius in enumerate([outer_radius, 20, 10]):
            alpha = 150 - i * 40
            color = (*self.accent_color[:3], alpha) if len(self.accent_color) == 3 else (*self.accent_color[:3], alpha)
            # Create surface for alpha support
            circle_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (100, 180, 255, alpha), (radius + 2, radius + 2), radius, 2)
            screen.blit(circle_surf, (x - radius - 2, y - radius - 2))
        
        # Draw crosshair lines
        line_length = 50
        line_color = (100, 180, 255, 200)
        
        # Create surface for alpha lines
        line_surf = pygame.Surface((line_length * 2 + 20, line_length * 2 + 20), pygame.SRCALPHA)
        center = line_length + 10
        
        # Horizontal lines (with gap in middle)
        pygame.draw.line(line_surf, line_color, (0, center), (center - 15, center), 2)
        pygame.draw.line(line_surf, line_color, (center + 15, center), (center * 2, center), 2)
        
        # Vertical lines (with gap in middle)
        pygame.draw.line(line_surf, line_color, (center, 0), (center, center - 15), 2)
        pygame.draw.line(line_surf, line_color, (center, center + 15), (center, center * 2), 2)
        
        screen.blit(line_surf, (x - center, y - center))
        
        # Draw "DROP HERE" text
        drop_text = self.font_small.render("DROP TO PLACE", True, (100, 180, 255))
        screen.blit(drop_text, (x - drop_text.get_width() // 2, y + 40))
        
        # Draw small info about the item
        if self.dragging_item:
            info_text = self.font_small.render(f"Mass: {self.dragging_item.mass:.2f}", True, (150, 150, 150))
            screen.blit(info_text, (x - info_text.get_width() // 2, y + 55))
