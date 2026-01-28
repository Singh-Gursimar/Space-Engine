"""3D Renderer for the space simulation using OpenGL."""

import math
from typing import List, Tuple
from OpenGL.GL import *
from OpenGL.GLU import *
from .celestial_body import CelestialBody
from .camera import Camera


class Renderer:
    """
    OpenGL renderer for the space simulation.
    Handles drawing celestial bodies, trails, and UI elements.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize the renderer.
        
        Args:
            width: Window width
            height: Window height
        """
        self.width = width
        self.height = height
        self.camera = Camera()
        
        # Sphere rendering quality
        self.sphere_slices = 32
        self.sphere_stacks = 32
        
        # Quadric for sphere rendering
        self.quadric = None
        
        # Visual settings
        self.show_trails = True
        self.show_grid = True
        self.show_axes = True
        self.trail_fade = True
        
        self._init_opengl()
    
    def _init_opengl(self) -> None:
        """Initialize OpenGL settings."""
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        
        # Enable smooth shading
        glShadeModel(GL_SMOOTH)
        
        # Set up lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        
        # Light properties
        light_position = [0.0, 100.0, 100.0, 1.0]
        light_ambient = [0.2, 0.2, 0.2, 1.0]
        light_diffuse = [1.0, 1.0, 1.0, 1.0]
        light_specular = [1.0, 1.0, 1.0, 1.0]
        
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)
        
        # Enable color material
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Line smoothing
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        # Create quadric for sphere rendering
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        
        # Set up projection
        self._setup_projection()
    
    def _setup_projection(self) -> None:
        """Set up the perspective projection matrix."""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        aspect = self.width / self.height if self.height > 0 else 1.0
        gluPerspective(60.0, aspect, 1.0, 50000.0)
        
        glMatrixMode(GL_MODELVIEW)
    
    def resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        self.width = width
        self.height = height
        glViewport(0, 0, width, height)
        self._setup_projection()
    
    def clear(self) -> None:
        """Clear the screen."""
        glClearColor(0.02, 0.02, 0.05, 1.0)  # Dark space background
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    def draw_body(self, body: CelestialBody) -> None:
        """
        Draw a celestial body.
        
        Args:
            body: The celestial body to draw
        """
        glPushMatrix()
        
        # Move to body position
        glTranslatef(body.position.x, body.position.y, body.position.z)
        
        # Set color
        if body.is_star:
            # Stars emit light - disable lighting for them
            glDisable(GL_LIGHTING)
            glColor3f(*body.color)
            
            # Draw glow effect
            self._draw_glow(body.radius * 1.5, body.color)
            
            glEnable(GL_LIGHTING)
        else:
            glColor3f(*body.color)
        
        # Draw selection indicator
        if body.is_selected:
            glDisable(GL_LIGHTING)
            glColor4f(1.0, 1.0, 0.0, 0.5)
            gluSphere(self.quadric, body.radius * 1.2, 16, 16)
            glEnable(GL_LIGHTING)
            glColor3f(*body.color)
        
        # Draw the sphere
        gluSphere(self.quadric, body.radius, self.sphere_slices, self.sphere_stacks)
        
        glPopMatrix()
    
    def _draw_glow(self, radius: float, color: Tuple[float, float, float]) -> None:
        """Draw a glow effect for stars."""
        glDisable(GL_DEPTH_TEST)
        
        # Draw multiple layers with decreasing opacity
        for i in range(5):
            scale = 1.0 + i * 0.3
            alpha = 0.3 - i * 0.05
            glColor4f(color[0], color[1], color[2], alpha)
            gluSphere(self.quadric, radius * scale, 16, 16)
        
        glEnable(GL_DEPTH_TEST)
    
    def draw_trail(self, body: CelestialBody) -> None:
        """
        Draw the orbital trail for a celestial body.
        
        Args:
            body: The celestial body whose trail to draw
        """
        if not self.show_trails or len(body.trail) < 2:
            return
        
        glDisable(GL_LIGHTING)
        glLineWidth(1.5)
        
        glBegin(GL_LINE_STRIP)
        
        for i, pos in enumerate(body.trail):
            # Fade trail from start to end
            if self.trail_fade:
                alpha = i / len(body.trail)
            else:
                alpha = 0.8
            
            glColor4f(body.color[0], body.color[1], body.color[2], alpha)
            glVertex3f(pos.x, pos.y, pos.z)
        
        # Connect to current position
        glColor4f(body.color[0], body.color[1], body.color[2], 1.0)
        glVertex3f(body.position.x, body.position.y, body.position.z)
        
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    def draw_grid(self, size: float = 1000.0, divisions: int = 20) -> None:
        """
        Draw a reference grid on the XZ plane.
        
        Args:
            size: Size of the grid
            divisions: Number of grid divisions
        """
        if not self.show_grid:
            return
        
        glDisable(GL_LIGHTING)
        glLineWidth(1.0)
        glColor4f(0.3, 0.3, 0.3, 0.3)
        
        step = size / divisions
        half_size = size / 2
        
        glBegin(GL_LINES)
        
        for i in range(divisions + 1):
            # Lines along X axis
            x = -half_size + i * step
            glVertex3f(x, 0, -half_size)
            glVertex3f(x, 0, half_size)
            
            # Lines along Z axis
            z = -half_size + i * step
            glVertex3f(-half_size, 0, z)
            glVertex3f(half_size, 0, z)
        
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    def draw_axes(self, length: float = 100.0) -> None:
        """
        Draw coordinate axes.
        
        Args:
            length: Length of each axis
        """
        if not self.show_axes:
            return
        
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        
        glBegin(GL_LINES)
        
        # X axis (red)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(length, 0, 0)
        
        # Y axis (green)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, length, 0)
        
        # Z axis (blue)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, length)
        
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    def draw_starfield(self, num_stars: int = 500) -> None:
        """
        Draw a background starfield.
        Note: Stars are at fixed positions, this is for visual effect only.
        """
        glDisable(GL_LIGHTING)
        glPointSize(1.5)
        
        glBegin(GL_POINTS)
        glColor3f(1.0, 1.0, 1.0)
        
        # Use deterministic positions based on index for consistency
        import random
        random.seed(42)
        
        for _ in range(num_stars):
            # Place stars on a distant sphere
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            r = 10000
            
            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.sin(phi) * math.sin(theta)
            z = r * math.cos(phi)
            
            brightness = random.uniform(0.3, 1.0)
            glColor3f(brightness, brightness, brightness)
            glVertex3f(x, y, z)
        
        glEnd()
        
        glEnable(GL_LIGHTING)
    
    def render(self, bodies: List[CelestialBody]) -> None:
        """
        Render the complete scene.
        
        Args:
            bodies: List of celestial bodies to render
        """
        self.clear()
        
        # Apply camera transformation
        self.camera.apply()
        
        # Draw background elements
        self.draw_starfield()
        self.draw_grid()
        self.draw_axes()
        
        # Draw trails first (so they appear behind bodies)
        for body in bodies:
            self.draw_trail(body)
        
        # Draw bodies
        for body in bodies:
            self.draw_body(body)
    
    def cleanup(self) -> None:
        """Clean up OpenGL resources."""
        if self.quadric:
            gluDeleteQuadric(self.quadric)
