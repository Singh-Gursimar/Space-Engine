"""3D Camera for viewing the simulation."""

import math
from OpenGL.GL import *
from OpenGL.GLU import *
from .vector3 import Vector3


class Camera:
    """
    A 3D camera for navigating the space simulation.
    Supports orbiting, panning, and zooming.
    """
    
    def __init__(self):
        """Initialize the camera with default settings."""
        # Camera position in spherical coordinates (for orbiting)
        self.distance = 500.0  # Distance from target
        self.azimuth = 45.0    # Horizontal angle (degrees)
        self.elevation = 30.0  # Vertical angle (degrees)
        
        # Target point (what the camera looks at)
        self.target = Vector3(0, 0, 0)
        
        # Camera settings
        self.min_distance = 10.0
        self.max_distance = 10000.0
        self.rotation_speed = 0.3
        self.pan_speed = 1.0
        self.zoom_speed = 1.1
        
        # Computed camera position
        self._position = Vector3(0, 0, 0)
        self._update_position()
    
    def _update_position(self) -> None:
        """Update camera position from spherical coordinates."""
        # Convert degrees to radians
        az_rad = math.radians(self.azimuth)
        el_rad = math.radians(self.elevation)
        
        # Spherical to Cartesian conversion
        self._position.x = self.target.x + self.distance * math.cos(el_rad) * math.sin(az_rad)
        self._position.y = self.target.y + self.distance * math.sin(el_rad)
        self._position.z = self.target.z + self.distance * math.cos(el_rad) * math.cos(az_rad)
    
    @property
    def position(self) -> Vector3:
        """Get the camera position."""
        return self._position
    
    def apply(self) -> None:
        """Apply the camera transformation to the OpenGL modelview matrix."""
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        gluLookAt(
            self._position.x, self._position.y, self._position.z,  # Camera position
            self.target.x, self.target.y, self.target.z,           # Look at target
            0.0, 1.0, 0.0                                          # Up vector
        )
    
    def rotate(self, delta_x: float, delta_y: float) -> None:
        """
        Rotate the camera around the target.
        
        Args:
            delta_x: Horizontal rotation amount
            delta_y: Vertical rotation amount
        """
        self.azimuth += delta_x * self.rotation_speed
        self.elevation -= delta_y * self.rotation_speed  # Inverted for natural feel
        
        # Clamp elevation to avoid gimbal lock
        self.elevation = max(-89.0, min(89.0, self.elevation))
        
        # Wrap azimuth
        self.azimuth = self.azimuth % 360.0
        
        self._update_position()
    
    def zoom(self, delta: float) -> None:
        """
        Zoom the camera in or out.
        
        Args:
            delta: Positive to zoom out, negative to zoom in
        """
        if delta > 0:
            self.distance *= self.zoom_speed
        else:
            self.distance /= self.zoom_speed
        
        # Clamp distance
        self.distance = max(self.min_distance, min(self.max_distance, self.distance))
        
        self._update_position()
    
    def pan(self, delta_x: float, delta_y: float) -> None:
        """
        Pan the camera (move the target).
        
        Args:
            delta_x: Horizontal pan amount
            delta_y: Vertical pan amount
        """
        # Calculate right and up vectors relative to camera orientation
        az_rad = math.radians(self.azimuth)
        
        # Right vector (perpendicular to view direction on XZ plane)
        right_x = math.cos(az_rad)
        right_z = -math.sin(az_rad)
        
        # Move target
        pan_scale = self.distance * self.pan_speed * 0.001
        self.target.x += (right_x * delta_x) * pan_scale
        self.target.z += (right_z * delta_x) * pan_scale
        self.target.y += delta_y * pan_scale
        
        self._update_position()
    
    def focus_on(self, position: Vector3, smooth: bool = False) -> None:
        """
        Focus the camera on a specific position.
        
        Args:
            position: The position to focus on
            smooth: Whether to smoothly transition (not implemented yet)
        """
        self.target = position.copy()
        self._update_position()
    
    def reset(self) -> None:
        """Reset the camera to default position."""
        self.distance = 500.0
        self.azimuth = 45.0
        self.elevation = 30.0
        self.target = Vector3(0, 0, 0)
        self._update_position()
