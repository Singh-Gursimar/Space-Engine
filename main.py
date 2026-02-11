"""
Space Engine - A 3D Physics Simulator for Space Objects
Create your own solar systems with realistic gravitational physics!

Controls:
    Mouse Drag      - Rotate camera / Look around
    Mouse Wheel     - Zoom in/out / Adjust move speed
    Middle Mouse    - Pan camera (orbit mode)
    F               - Toggle Free/Orbit camera mode
    WASD            - Move camera (free mode)
    Q/E             - Move down/up (free mode)
    SPACE           - Pause/Resume simulation
    +/-             - Adjust time scale
    M               - Toggle menu
    K               - Toggle collisions
    H               - Show help
    R               - Reset camera
    ESC             - Quit
"""

import sys
import math
import pygame
from pygame.locals import (
    DOUBLEBUF, OPENGL, RESIZABLE, QUIT, VIDEORESIZE, 
    MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL,
    KEYDOWN, K_ESCAPE, K_SPACE, 
    K_w, K_a, K_s, K_d, K_q, K_e, K_f, K_h, K_i, K_m, K_r, K_g, K_t, K_c, K_k,
    K_PLUS, K_EQUALS, K_MINUS, 
    K_LEFTBRACKET, K_RIGHTBRACKET, K_BACKSPACE,
    K_0, K_1, K_2, K_3, K_4
)
from OpenGL.GL import glViewport, glMatrixMode, glLoadIdentity, glEnable, glDisable, glClear, glFlush, glGetDoublev, glGetIntegerv, glGenTextures, glBindTexture, glTexParameteri, glTexImage2D, glBegin, glEnd, glTexCoord2f, glVertex2f, glBlendFunc, glPushMatrix, glPopMatrix, glOrtho, glColor4f, glDeleteTextures, GL_PROJECTION, GL_MODELVIEW, GL_MODELVIEW_MATRIX, GL_PROJECTION_MATRIX, GL_VIEWPORT, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_TEXTURE_2D, GL_LINEAR, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_RGBA, GL_UNSIGNED_BYTE, GL_QUADS, GL_LIGHTING  # type: ignore
from OpenGL.GLU import gluPerspective, gluUnProject  # type: ignore
from typing import Dict, Any, Optional, Tuple

from src.physics import PhysicsEngine
from src.renderer import Renderer
from src.ui import UI
from src.menu import Menu, PresetItem
from src.celestial_body import CelestialBody
from src.vector3 import Vector3
from src import solar_system


class SpaceEngine:
    """Main application class for the Space Engine simulator."""
    
    def __init__(self, width: int = 1280, height: int = 720):
        """
        Initialize the Space Engine.
        
        Args:
            width: Window width
            height: Window height
        """
        self.width = width
        self.height = height
        self.running = True
        
        # Initialize Pygame
        pygame.init()
        pygame.display.set_caption("Space Engine - 3D Physics Simulator")
        
        # Set up OpenGL display
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL | RESIZABLE)
        
        # Initialize components
        self.physics = PhysicsEngine(time_scale=1.0)
        self.renderer = Renderer(width, height)
        self.ui = UI(width, height)
        self.menu = Menu(width, height)
        
        # Set up presets in menu
        self._setup_presets()
        
        # Clock for FPS control
        self.clock = pygame.time.Clock()
        self.target_fps = 60
        self.current_fps = 60.0
        
        # Mouse state
        self.mouse_dragging = False
        self.mouse_panning = False
        self.last_mouse_pos = (0, 0)
        
        # Selected body
        self.selected_body = None
        
        # Body counter for unique names
        self.body_counter = 0
        
        # Load default solar system
        solar_system.create_solar_system(self.physics)
        
        print("Space Engine initialized!")
        print("Press H for help, ESC to quit")
    
    def _setup_presets(self) -> None:
        """Set up preset systems in the menu."""
        presets = [
            PresetItem("Solar System", "Our solar system", lambda: self._load_preset("solar")),
            PresetItem("Binary Stars", "Two orbiting stars", lambda: self._load_preset("binary")),
            PresetItem("Earth & Moon", "Earth-Moon system", lambda: self._load_preset("earth_moon")),
            PresetItem("Random System", "Randomly generated", lambda: self._load_preset("random")),
            PresetItem("Clear All", "Empty space", lambda: self._load_preset("clear")),
        ]
        self.menu.set_presets(presets)
    
    def handle_events(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                continue
            
            # Let menu handle events first
            menu_result = self.menu.handle_event(event)
            if menu_result:
                self._handle_menu_action(menu_result)
                continue
            
            # Skip camera controls if menu is handling drag
            if self.menu.is_dragging():
                continue
            
            if event.type == VIDEORESIZE:
                self._handle_resize(event.w, event.h)
            
            elif event.type == KEYDOWN:
                self._handle_keydown(event)
            
            elif event.type == MOUSEBUTTONDOWN:
                # Don't start camera drag if clicking on menu
                if not self.menu.point_in_menu(event.pos):
                    self._handle_mouse_down(event)
            
            elif event.type == MOUSEBUTTONUP:
                self._handle_mouse_up(event)
            
            elif event.type == MOUSEMOTION:
                self._handle_mouse_motion(event)
            
            elif event.type == MOUSEWHEEL:
                # Only zoom if not over menu
                if not self.menu.point_in_menu(pygame.mouse.get_pos()):
                    self._handle_mouse_wheel(event)
    
    def _handle_menu_action(self, action: Dict[str, Any]) -> None:
        """Handle actions from the menu."""
        if action["action"] == "load_preset":
            preset = action["preset"]
            preset.loader()
        
        elif action["action"] == "add_body":
            self._add_body_at_screen_pos(action["item"], action["screen_pos"])
    
    def _add_body_at_screen_pos(self, item: CelestialBody, screen_pos: Tuple[float, float]) -> None:
        """
        Add a celestial body at a screen position.
        Projects the screen position into 3D space.
        """
        position = self._screen_to_world_pos(screen_pos)
        
        # Calculate orbital velocity if there's a central body
        velocity = Vector3(0, 0, 0)
        if self.physics.bodies:
            # Find the most massive body (likely the star)
            central_body = max(self.physics.bodies, key=lambda b: b.mass)
            
            # Calculate distance to central body
            direction = position - central_body.position
            distance = direction.magnitude
            
            if distance > 0 and not item.is_star:
                # Calculate orbital velocity
                orbital_speed = math.sqrt(CelestialBody.G * central_body.mass / distance)
                
                # Perpendicular direction for orbit (cross with up)
                up = Vector3(0, 1, 0)
                tangent = direction.cross(up)
                
                # If tangent is zero (direction parallel to up), use a different perpendicular
                if tangent.magnitude < 0.001:
                    tangent = direction.cross(Vector3(1, 0, 0))
                
                tangent = tangent.normalize()
                velocity = tangent * orbital_speed
        
        # Create unique name
        self.body_counter += 1
        name = f"{item.name}_{self.body_counter}"
        
        # Create and add the body
        body = CelestialBody(
            name=name,
            mass=item.mass,
            radius=item.radius,
            position=position,
            velocity=velocity,
            color=item.color,
            is_star=item.is_star
        )
        
        self.physics.add_body(body)
        print(f"Added {name} at position {position}")
    
    def _screen_to_world_pos(self, screen_pos: tuple[float, float]) -> Vector3:
        """
        Convert a screen position to a 3D world position on the Y=0 plane using raycasting.
        
        Args:
            screen_pos: (x, y) screen coordinates
            
        Returns:
            Vector3 world position on the orbital plane
        """
        x, y = screen_pos
        # OpenGL Y is inverted relative to window Y
        y = self.height - y
        
        try:
            # Get matrices
            modelview: Any = glGetDoublev(GL_MODELVIEW_MATRIX)  # type: ignore
            projection: Any = glGetDoublev(GL_PROJECTION_MATRIX)  # type: ignore
            viewport: Any = glGetIntegerv(GL_VIEWPORT)  # type: ignore
            
            # Unproject two points to get the ray
            # Point on near plane (z=0)
            near_point = gluUnProject(x, y, 0.0, modelview, projection, viewport)
            # Point on far plane (z=1)
            far_point = gluUnProject(x, y, 1.0, modelview, projection, viewport)
            
            ray_origin = Vector3(near_point[0], near_point[1], near_point[2])
            ray_end = Vector3(far_point[0], far_point[1], far_point[2])
            
            ray_direction = ray_end - ray_origin
            
            # Intersect with Plane Y=0
            # Plane normal N = (0, 1, 0)
            # t = -dot(Origin, N) / dot(Direction, N) = -Origin.y / Direction.y
            
            if abs(ray_direction.y) < 1e-6:
                # Ray is parallel to plane, return target projection as fallback
                return Vector3(self.renderer.camera.target.x, 0, self.renderer.camera.target.z)
                
            t = -ray_origin.y / ray_direction.y
            
            intersection = ray_origin + ray_direction * t
            return intersection
            
        except Exception as e:
            # Fallback if GL calls fail
            print(f"Error in screen projection: {e}")
            return Vector3(0, 0, 0)
    
    def _get_placement_position(self) -> Optional[Tuple[float, float, float]]:
        """
        Get the 3D placement position if currently dragging.
        
        Returns:
            (x, y, z) tuple or None if not dragging
        """
        if self.menu.is_dragging() and not self.menu.point_in_menu(self.menu.drag_pos):
            pos = self._screen_to_world_pos(self.menu.drag_pos)
            return (pos.x, pos.y, pos.z)
        return None
    
    def _handle_resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        self.width = width
        self.height = height
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL | RESIZABLE)
        self.renderer.resize(width, height)
        self.ui.resize(width, height)
        self.menu.resize(width, height)
    
    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Handle keyboard input."""
        key = event.key
        
        if key == K_ESCAPE:
            self.running = False
        
        elif key == K_SPACE:
            self.physics.toggle_pause()
        
        elif key == K_h:
            self.ui.toggle_help()
        
        elif key == K_i:
            self.ui.toggle_info()
        
        elif key == K_m:
            self.menu.toggle_menu()
        
        elif key == K_r:
            self.renderer.camera.reset()
        
        elif key == K_f:
            mode = self.renderer.camera.toggle_mode()
            print(f"Camera mode: {mode.upper()} (WASD to move, QE for up/down)" if mode == 'free' else "Camera mode: ORBIT")
        
        elif key == K_g:
            self.renderer.show_grid = not self.renderer.show_grid
        
        elif key == K_t:
            self.renderer.show_trails = not self.renderer.show_trails
        
        elif key == K_c:
            for body in self.physics.bodies:
                body.clear_trail()
        
        elif key == K_k:
            self.physics.collisions_enabled = not self.physics.collisions_enabled
            status = "enabled" if self.physics.collisions_enabled else "disabled"
            print(f"Collisions {status}")
        
        elif key == K_PLUS or key == K_EQUALS:
            self.physics.set_time_scale(self.physics.time_scale * 2.0)
            print(f"Time scale: {self.physics.time_scale:.1f}x")
        
        elif key == K_MINUS:
            self.physics.set_time_scale(self.physics.time_scale / 2.0)
            print(f"Time scale: {self.physics.time_scale:.1f}x")
        
        elif key == K_LEFTBRACKET:
            # Slow down a lot
            self.physics.set_time_scale(self.physics.time_scale / 5.0)
            print(f"Time scale: {self.physics.time_scale:.2f}x")
        
        elif key == K_RIGHTBRACKET:
            # Speed up a lot
            self.physics.set_time_scale(self.physics.time_scale * 5.0)
            print(f"Time scale: {self.physics.time_scale:.1f}x")
        
        elif key == K_BACKSPACE:
            # Remove the last added body
            if self.physics.bodies:
                removed = self.physics.bodies.pop()
                print(f"Removed {removed.name}")
        
        # Preset systems
        elif key == K_1:
            self._load_preset("solar")
        elif key == K_2:
            self._load_preset("binary")
        elif key == K_3:
            self._load_preset("earth_moon")
        elif key == K_4:
            self._load_preset("random")
        elif key == K_0:
            self._load_preset("clear")
    
    def _load_preset(self, preset_name: str) -> None:
        """Load a preset solar system."""
        self.physics.clear()
        self.selected_body = None
        
        if preset_name == "solar":
            solar_system.create_solar_system(self.physics)
            self.renderer.camera.distance = 800
            self.renderer.camera.elevation = 45
        elif preset_name == "binary":
            solar_system.create_binary_star_system(self.physics)
            self.renderer.camera.distance = 700
            self.renderer.camera.elevation = 40
        elif preset_name == "earth_moon":
            solar_system.create_earth_moon_system(self.physics)
            self.renderer.camera.distance = 300
            self.renderer.camera.elevation = 35
        elif preset_name == "random":
            solar_system.create_random_system(self.physics, num_bodies=8)
            self.renderer.camera.distance = 600
            self.renderer.camera.elevation = 45
        elif preset_name == "clear":
            self.renderer.camera.distance = 500
        
        self.renderer.camera.target = Vector3(0, 0, 0)
        self.renderer.camera.azimuth = 45
        if self.renderer.camera.mode == 'orbit':
            self.renderer.camera._update_position()  # type: ignore
    
    def _handle_mouse_down(self, event: pygame.event.Event) -> None:
        """Handle mouse button press."""
        if event.button == 1:  # Left click
            self.mouse_dragging = True
            self.last_mouse_pos = event.pos
        elif event.button == 2:  # Middle click
            self.mouse_panning = True
            self.last_mouse_pos = event.pos
        elif event.button == 3:  # Right click
            # Could be used for context menu or body selection
            pass
    
    def _handle_mouse_up(self, event: pygame.event.Event) -> None:
        """Handle mouse button release."""
        if event.button == 1:
            self.mouse_dragging = False
        elif event.button == 2:
            self.mouse_panning = False
    
    def _handle_mouse_motion(self, event: pygame.event.Event) -> None:
        """Handle mouse movement."""
        if self.mouse_dragging:
            dx = event.pos[0] - self.last_mouse_pos[0]
            dy = event.pos[1] - self.last_mouse_pos[1]
            self.renderer.camera.rotate(dx, dy)
            self.last_mouse_pos = event.pos
        
        elif self.mouse_panning:
            dx = event.pos[0] - self.last_mouse_pos[0]
            dy = event.pos[1] - self.last_mouse_pos[1]
            self.renderer.camera.pan(-dx, dy)
            self.last_mouse_pos = event.pos
    
    def _handle_mouse_wheel(self, event: pygame.event.Event) -> None:
        """Handle mouse wheel scroll."""
        self.renderer.camera.zoom(-event.y)
    
    def update(self, dt: float) -> None:
        """
        Update the simulation.
        
        Args:
            dt: Delta time in seconds
        """
        # Handle camera movement in free mode
        if self.renderer.camera.mode == 'free':
            keys = pygame.key.get_pressed()
            forward = 0.0
            right = 0.0
            up = 0.0
            
            if keys[K_w]:
                forward += 1.0
            if keys[K_s]:
                forward -= 1.0
            if keys[K_d]:
                right += 1.0
            if keys[K_a]:
                right -= 1.0
            if keys[K_e]:
                up += 1.0
            if keys[K_q]:
                up -= 1.0
            
            # Apply movement
            if forward != 0 or right != 0 or up != 0:
                self.renderer.camera.move(forward, right, up, dt)
        
        self.physics.update(dt)
    
    def render(self) -> None:
        """Render the scene."""
        # Get placement position if dragging
        placement_pos = self._get_placement_position()
        if placement_pos is None:
            placement_pos = (0.0, 0.0, 0.0)  # Provide default value
        
        # Render 3D scene with particles and placement indicator
        self.renderer.render(self.physics.bodies, self.physics.particles, placement_pos)
        
        # Switch to 2D for UI
        self._setup_2d()
        
        # Create a surface for 2D rendering
        ui_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ui_surface.fill((0, 0, 0, 0))
        
        # Get camera info for UI
        camera = self.renderer.camera
        camera_info: Dict[str, Any] = {
            'mode': camera.mode,
            'distance': camera.distance,
            'azimuth': camera.azimuth,
            'elevation': camera.elevation,
            'speed': camera.move_speed
        }
        
        # Render UI elements
        self.ui.render(ui_surface, self.physics, self.current_fps, self.selected_body, camera_info)
        
        # Render menu
        self.menu.render(ui_surface)
        
        # Blit UI surface to screen using OpenGL
        self._render_ui_surface(ui_surface)
        
        # Swap buffers
        pygame.display.flip()
    
    def _setup_2d(self) -> None:
        """Set up OpenGL for 2D rendering."""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        # Match pygame coordinate system: origin at top-left
        glOrtho(0, self.width, self.height, 0, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
    
    def _render_ui_surface(self, surface: pygame.Surface) -> None:
        """Render a Pygame surface using OpenGL."""
        # Convert surface to raw pixel data (no flip needed)
        texture_data = pygame.image.tostring(surface, "RGBA", False)
        
        # Create texture
        glEnable(GL_TEXTURE_2D)
        texture_id: int = glGenTextures(1)  # type: ignore
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 
                     0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        # Draw textured quad
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        # Map texture so top-left of texture goes to top-left of screen
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(self.width, 0)
        glTexCoord2f(1, 1); glVertex2f(self.width, self.height)
        glTexCoord2f(0, 1); glVertex2f(0, self.height)
        glEnd()
        
        glDisable(GL_TEXTURE_2D)
        glDeleteTextures([texture_id])
        
        # Restore 3D rendering state
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
    
    def run(self) -> None:
        """Main game loop."""
        print("\n" + "="*50)
        print("SPACE ENGINE - 3D Physics Simulator")
        print("="*50)
        print("Creating your own solar systems...")
        print("\nControls:")
        print("  Drag mouse    - Rotate view")
        print("  Scroll wheel  - Zoom")
        print("  SPACE         - Pause/Resume")
        print("  M             - Toggle menu")
        print("  H             - Help")
        print("  ESC           - Quit")
        print("\nUse the sidebar menu to add objects!")
        print("="*50 + "\n")
        
        while self.running:
            # Calculate delta time (cap to prevent instability on lag spikes)
            dt = min(self.clock.tick(self.target_fps) / 1000.0, 0.05)
            self.current_fps = self.clock.get_fps()
            
            # Handle events
            self.handle_events()
            
            # Update simulation
            self.update(dt)
            
            # Render
            self.render()
        
        # Cleanup
        self.renderer.cleanup()
        pygame.quit()


def main():
    """Entry point for the application."""
    try:
        engine = SpaceEngine()
        engine.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()
