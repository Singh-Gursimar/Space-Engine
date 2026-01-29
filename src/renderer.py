"""3D Renderer for the space simulation using OpenGL."""

import math
from typing import List, Tuple, TYPE_CHECKING
from OpenGL.GL import *
from OpenGL.GLU import *
from .celestial_body import CelestialBody
from .camera import Camera

if TYPE_CHECKING:
    from .particles import ParticleSystem


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
        
        # Sphere rendering quality (reduced for performance)
        self.sphere_slices = 16
        self.sphere_stacks = 16
        
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
        
        # Main light (sun-like, from center)
        light_position = [0.0, 50.0, 0.0, 1.0]  # Positional light at origin
        light_ambient = [0.15, 0.15, 0.18, 1.0]  # Slight blue-ish ambient
        light_diffuse = [1.0, 0.95, 0.9, 1.0]  # Warm white
        light_specular = [1.0, 1.0, 1.0, 1.0]
        
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)
        
        # Light attenuation for more realistic falloff
        glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.0001)
        glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.000001)
        
        # Enable color material
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Line smoothing
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        # Point smoothing
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
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
        """Clear the screen with a deep space gradient-like background."""
        glClearColor(0.01, 0.01, 0.03, 1.0)  # Very dark blue-black
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
        
        # Check for special body types by name
        is_black_hole = 'black hole' in body.name.lower()
        is_neutron_star = 'neutron' in body.name.lower()
        
        if is_black_hole:
            # Black holes: dark with accretion disk effect
            glDisable(GL_LIGHTING)
            
            # Dark core
            glColor3f(0.0, 0.0, 0.0)
            gluSphere(self.quadric, body.radius, 12, 12)
            
            # Event horizon glow
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            glColor4f(0.5, 0.2, 0.8, 0.3)
            gluSphere(self.quadric, body.radius * 1.5, 12, 12)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            glEnable(GL_LIGHTING)
        elif is_neutron_star:
            # Neutron stars: small, bright, pulsing
            glDisable(GL_LIGHTING)
            
            import time
            pulse = 0.7 + 0.3 * abs(math.sin(time.time() * 10))
            
            # Bright core
            glColor3f(0.8 * pulse, 0.9 * pulse, 1.0 * pulse)
            gluSphere(self.quadric, body.radius, 12, 12)
            
            # Glow
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            glColor4f(0.6, 0.8, 1.0, 0.4 * pulse)
            gluSphere(self.quadric, body.radius * 2, 8, 8)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            glEnable(GL_LIGHTING)
        elif body.is_star:
            # Stars: bright, self-illuminated (simplified glow)
            glDisable(GL_LIGHTING)
            
            # Simple 2-layer glow effect
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            glColor4f(body.color[0], body.color[1], body.color[2], 0.2)
            gluSphere(self.quadric, body.radius * 1.5, 12, 12)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            # Draw solid core
            glColor3f(*body.color)
            gluSphere(self.quadric, body.radius, self.sphere_slices, self.sphere_stacks)
            
            glEnable(GL_LIGHTING)
        else:
            # Planets: lit by stars with outline for visibility
            glEnable(GL_LIGHTING)
            glColor3f(*body.color)
            
            # Selection indicator
            if body.is_selected:
                glDisable(GL_LIGHTING)
                glColor4f(1.0, 1.0, 0.0, 0.3)
                gluSphere(self.quadric, body.radius * 1.2, 12, 12)
                glEnable(GL_LIGHTING)
                glColor3f(*body.color)
            
            # Draw the sphere
            gluSphere(self.quadric, body.radius, self.sphere_slices, self.sphere_stacks)
            
            # Draw bright outline ring for visibility
            glDisable(GL_LIGHTING)
            glEnable(GL_BLEND)
            glColor4f(body.color[0] * 1.5, body.color[1] * 1.5, body.color[2] * 1.5, 0.6)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            for i in range(24):
                angle = 2 * math.pi * i / 24
                glVertex3f(body.radius * 1.05 * math.cos(angle), 0, body.radius * 1.05 * math.sin(angle))
            glEnd()
            glEnable(GL_LIGHTING)
        
        glPopMatrix()
    
    def _draw_corona(self, radius: float, color: Tuple[float, float, float]) -> None:
        """Draw a beautiful corona effect for stars."""
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending for glow
        
        # Outer glow layers
        for i in range(8):
            scale = 1.0 + i * 0.4
            alpha = 0.15 - i * 0.015
            # Slightly shift color toward white for inner glow
            r = min(1.0, color[0] + i * 0.05)
            g = min(1.0, color[1] + i * 0.03)
            b = min(1.0, color[2] + i * 0.02)
            glColor4f(r, g, b, max(0, alpha))
            gluSphere(self.quadric, radius * scale, 16, 16)
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
    
    def _draw_atmosphere(self, radius: float, color: Tuple[float, float, float]) -> None:
        """Draw a subtle atmosphere effect around planets."""
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Thin atmospheric layer
        atm_color = (
            min(1.0, color[0] * 0.5 + 0.3),
            min(1.0, color[1] * 0.5 + 0.4),
            min(1.0, color[2] * 0.5 + 0.5)
        )
        glColor4f(atm_color[0], atm_color[1], atm_color[2], 0.15)
        gluSphere(self.quadric, radius * 1.08, 20, 20)
        
        glEnable(GL_LIGHTING)
    
    def draw_trail(self, body: CelestialBody) -> None:
        """
        Draw a beautiful orbital trail for a celestial body.
        
        Args:
            body: The celestial body whose trail to draw
        """
        if not self.show_trails or len(body.trail) < 2:
            return
        
        glDisable(GL_LIGHTING)
        
        # Draw trail with varying width for depth effect
        n_points = len(body.trail)
        
        # Draw as line strip with gradient
        glBegin(GL_LINE_STRIP)
        
        for i, pos in enumerate(body.trail):
            # Progress from 0 (oldest) to 1 (newest)
            progress = i / n_points
            
            # Fade alpha from start to end
            if self.trail_fade:
                alpha = progress * 0.8
            else:
                alpha = 0.6
            
            # Slightly brighten color toward the end
            r = min(1.0, body.color[0] * (0.5 + progress * 0.5))
            g = min(1.0, body.color[1] * (0.5 + progress * 0.5))
            b = min(1.0, body.color[2] * (0.5 + progress * 0.5))
            
            glColor4f(r, g, b, alpha)
            glVertex3f(pos.x, pos.y, pos.z)
        
        # Connect to current position with full brightness
        glColor4f(body.color[0], body.color[1], body.color[2], 1.0)
        glVertex3f(body.position.x, body.position.y, body.position.z)
        
        glEnd()
        
        # Draw a second pass with thinner brighter line for glow effect
        glLineWidth(1.0)
        glBegin(GL_LINE_STRIP)
        
        for i, pos in enumerate(body.trail[-50:] if len(body.trail) > 50 else body.trail):
            progress = i / min(50, len(body.trail))
            alpha = progress * 0.4
            glColor4f(1.0, 1.0, 1.0, alpha * 0.3)
            glVertex3f(pos.x, pos.y, pos.z)
        
        glVertex3f(body.position.x, body.position.y, body.position.z)
        glEnd()
        
        glLineWidth(2.0)
        glEnable(GL_LIGHTING)
    
    def draw_grid(self, size: float = 1500.0, divisions: int = 30) -> None:
        """
        Draw a reference grid on the XZ plane with distance rings.
        
        Args:
            size: Size of the grid
            divisions: Number of grid divisions
        """
        if not self.show_grid:
            return
        
        glDisable(GL_LIGHTING)
        glLineWidth(1.0)
        
        step = size / divisions
        half_size = size / 2
        
        # Draw grid lines
        glBegin(GL_LINES)
        
        for i in range(divisions + 1):
            dist_from_center = abs(i - divisions / 2) / (divisions / 2)
            alpha = 0.3 * (1.0 - dist_from_center * 0.5)
            
            # Highlight center lines (axes)
            if i == divisions // 2:
                glColor4f(0.5, 0.5, 0.6, 0.6)
            else:
                glColor4f(0.3, 0.35, 0.45, alpha)
            
            # Lines along X axis
            x = -half_size + i * step
            glVertex3f(x, 0, -half_size)
            glVertex3f(x, 0, half_size)
            
            # Lines along Z axis
            z = -half_size + i * step
            glVertex3f(-half_size, 0, z)
            glVertex3f(half_size, 0, z)
        
        glEnd()
        
        # Draw distance rings at 100, 200, 300, 400, 500 units
        glLineWidth(1.5)
        segments = 64
        for ring_dist in [100, 200, 300, 400, 500]:
            alpha = 0.5 - (ring_dist / 2000)
            glColor4f(0.4, 0.7, 1.0, max(0.15, alpha))
            glBegin(GL_LINE_LOOP)
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                glVertex3f(ring_dist * math.cos(angle), 0, ring_dist * math.sin(angle))
            glEnd()
        
        # Draw origin marker (bright cross at center)
        glLineWidth(3.0)
        glColor4f(1.0, 1.0, 1.0, 0.9)
        marker_size = 20
        glBegin(GL_LINES)
        glVertex3f(-marker_size, 0, 0)
        glVertex3f(marker_size, 0, 0)
        glVertex3f(0, 0, -marker_size)
        glVertex3f(0, 0, marker_size)
        glVertex3f(0, -marker_size, 0)
        glVertex3f(0, marker_size, 0)
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
        Draw a simple background starfield.
        """
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        # Use deterministic positions based on index for consistency
        import random
        random.seed(42)
        
        # Draw distant stars as simple points
        glPointSize(1.0)
        glBegin(GL_POINTS)
        
        for i in range(num_stars):
            # Place stars on a distant sphere
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            r = 15000
            
            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.sin(phi) * math.sin(theta)
            z = r * math.cos(phi)
            
            brightness = random.uniform(0.3, 1.0)
            glColor3f(brightness, brightness, brightness)
            glVertex3f(x, y, z)
        
        glEnd()
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
    
    def draw_particles(self, particle_system: 'ParticleSystem') -> None:
        """
        Draw all particles from the particle system.
        
        Args:
            particle_system: The particle system to render
        """
        if not particle_system.particles:
            return
        
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending
        
        glPointSize(3.0)
        glBegin(GL_POINTS)
        
        for particle in particle_system.particles:
            alpha = particle.alpha
            glColor4f(particle.color[0], particle.color[1], particle.color[2], alpha)
            glVertex3f(particle.position.x, particle.position.y, particle.position.z)
        
        glEnd()
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LIGHTING)
    
    def draw_placement_indicator(self, position: Tuple[float, float, float], 
                                  radius: float = 10.0, 
                                  color: Tuple[float, float, float] = (0.3, 0.8, 1.0)) -> None:
        """
        Draw a 3D placement indicator at the specified position.
        
        Args:
            position: 3D position (x, y, z) for the indicator
            radius: Size of the indicator
            color: RGB color tuple
        """
        import time
        pulse = abs(math.sin(time.time() * 5)) * 0.3 + 0.7
        
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(2.0)
        
        x, y, z = position
        
        glPushMatrix()
        glTranslatef(x, y, z)
        
        # Draw pulsing ring in XZ plane
        segments = 32
        ring_radius = radius * 2 * pulse
        
        glColor4f(color[0], color[1], color[2], 0.6 * pulse)
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            glVertex3f(math.cos(angle) * ring_radius, 0, math.sin(angle) * ring_radius)
        glEnd()
        
        # Draw inner solid ring
        glColor4f(1.0, 1.0, 1.0, 0.8)
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            glVertex3f(math.cos(angle) * radius, 0, math.sin(angle) * radius)
        glEnd()
        
        # Draw crosshairs
        line_len = radius * 3
        glColor4f(color[0], color[1], color[2], 0.5)
        glBegin(GL_LINES)
        glVertex3f(-line_len, 0, 0); glVertex3f(line_len, 0, 0)
        glVertex3f(0, 0, -line_len); glVertex3f(0, 0, line_len)
        glVertex3f(0, -line_len, 0); glVertex3f(0, line_len, 0)
        glEnd()
        
        # Center sphere
        glColor4f(color[0], color[1], color[2], 0.9)
        gluSphere(self.quadric, radius * 0.3, 8, 8)
        
        glPopMatrix()
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
    
    def render(self, bodies: List[CelestialBody], particle_system: 'ParticleSystem' = None,
               placement_pos: Tuple[float, float, float] = None) -> None:
        """
        Render the complete scene.
        
        Args:
            bodies: List of celestial bodies to render
            particle_system: Optional particle system for effects
            placement_pos: Optional 3D position for placement indicator
        """
        self.clear()
        
        # Apply camera transformation
        self.camera.apply()
        
        # Update light position to follow first star (if any)
        star_pos = [0.0, 100.0, 100.0, 1.0]
        for body in bodies:
            if body.is_star:
                star_pos = [body.position.x, body.position.y + 10, body.position.z, 1.0]
                break
        glLightfv(GL_LIGHT0, GL_POSITION, star_pos)
        
        # Draw background elements
        self.draw_starfield()
        self.draw_grid()
        self.draw_axes()
        
        # Draw trails
        glDisable(GL_LIGHTING)
        for body in bodies:
            self.draw_trail(body)
        glEnable(GL_LIGHTING)
        
        # Draw all bodies
        for body in bodies:
            self.draw_body(body)
        
        # Draw particles
        if particle_system and particle_system.particles:
            self.draw_particles(particle_system)
        
        # Draw placement indicator if dragging
        if placement_pos:
            self.draw_placement_indicator(placement_pos)
    
    def cleanup(self) -> None:
        """Clean up OpenGL resources."""
        if self.quadric:
            gluDeleteQuadric(self.quadric)
