"""3D Camera for viewing the simulation."""

import math
from OpenGL.GL import *
from OpenGL.GLU import *
from .vector3 import Vector3


class Camera:
    """
    A 3D camera for navigating the space simulation.
    Supports both orbit mode and free-fly mode.
    """
    
    def __init__(self):
        """Initialize the camera with default settings."""
        # Camera mode: 'orbit' or 'free'
        self.mode = 'orbit'
        
        # Orbit mode - Camera position in spherical coordinates
        self.distance = 500.0  # Distance from target
        self.azimuth = 45.0    # Horizontal angle (degrees)
        self.elevation = 30.0  # Vertical angle (degrees)
        self.target = Vector3(0, 0, 0)  # Target point (what the camera looks at)
        
        # Free mode - Direct camera control
        self._position = Vector3(350, 250, 350)  # Direct position
        self.yaw = -135.0      # Horizontal look angle (degrees)
        self.pitch = -30.0     # Vertical look angle (degrees)
        self.forward = Vector3(0, 0, -1)  # Forward direction
        self.right = Vector3(1, 0, 0)     # Right direction
        self.up = Vector3(0, 1, 0)        # Up direction
        
        # Camera settings
        self.min_distance = 10.0
        self.max_distance = 10000.0
        self.rotation_speed = 0.3
        self.look_speed = 0.15  # For free look
        self.move_speed = 100.0  # Units per second
        self.pan_speed = 1.0
        self.zoom_speed = 1.1
        
        self._update_position()
    
    def _update_position(self) -> None:
        """Update camera position and directions based on current mode."""
        if self.mode == 'orbit':
            # Convert degrees to radians
            az_rad = math.radians(self.azimuth)
            el_rad = math.radians(self.elevation)
            
            # Spherical to Cartesian conversion
            self._position.x = self.target.x + self.distance * math.cos(el_rad) * math.sin(az_rad)
            self._position.y = self.target.y + self.distance * math.sin(el_rad)
            self._position.z = self.target.z + self.distance * math.cos(el_rad) * math.cos(az_rad)
        else:
            # Free mode - update direction vectors from yaw and pitch
            yaw_rad = math.radians(self.yaw)
            pitch_rad = math.radians(self.pitch)
            
            # Calculate forward vector
            self.forward.x = math.cos(pitch_rad) * math.cos(yaw_rad)
            self.forward.y = math.sin(pitch_rad)
            self.forward.z = math.cos(pitch_rad) * math.sin(yaw_rad)
            self.forward = self.forward.normalize()
            
            # Calculate right vector (perpendicular to forward and world up)
            world_up = Vector3(0, 1, 0)
            self.right = self.forward.cross(world_up).normalize()
            
            # Calculate up vector
            self.up = self.right.cross(self.forward).normalize()
    
    @property
    def position(self) -> Vector3:
        """Get the camera position."""
        return self._position
    
    def apply(self) -> None:
        """Apply the camera transformation to the OpenGL modelview matrix."""
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        if self.mode == 'orbit':
            gluLookAt(
                self._position.x, self._position.y, self._position.z,  # Camera position
                self.target.x, self.target.y, self.target.z,           # Look at target
                0.0, 1.0, 0.0                                          # Up vector
            )
        else:
            # Free mode - look in the direction of forward vector
            look_at = self._position + self.forward
            gluLookAt(
                self._position.x, self._position.y, self._position.z,  # Camera position
                look_at.x, look_at.y, look_at.z,                       # Look at point
                self.up.x, self.up.y, self.up.z                        # Up vector
            )
    
    def rotate(self, delta_x: float, delta_y: float) -> None:
        """
        Rotate the camera (orbit mode) or look around (free mode).
        
        Args:
            delta_x: Horizontal rotation amount
            delta_y: Vertical rotation amount
        """
        if self.mode == 'orbit':
            self.azimuth += delta_x * self.rotation_speed
            self.elevation -= delta_y * self.rotation_speed  # Inverted for natural feel
            
            # Clamp elevation to avoid gimbal lock
            self.elevation = max(-89.0, min(89.0, self.elevation))
            
            # Wrap azimuth
            self.azimuth = self.azimuth % 360.0
        else:
            # Free look
            self.yaw += delta_x * self.look_speed
            self.pitch -= delta_y * self.look_speed  # Inverted for natural feel
            
            # Clamp pitch
            self.pitch = max(-89.0, min(89.0, self.pitch))
            
            # Wrap yaw
            self.yaw = self.yaw % 360.0
        
        self._update_position()
    
    def move(self, forward: float, right: float, up: float, dt: float) -> None:
        """
        Move the camera in free mode (WASD controls).
        
        Args:
            forward: Forward/backward movement (-1 to 1)
            right: Left/right movement (-1 to 1)
            up: Up/down movement (-1 to 1)
            dt: Delta time for smooth movement
        """
        if self.mode != 'free':
            return
        
        speed = self.move_speed * dt
        
        # Move along forward direction
        if forward != 0:
            self._position = self._position + self.forward * (forward * speed)
        
        # Move along right direction
        if right != 0:
            self._position = self._position + self.right * (right * speed)
        
        # Move along up direction (world up, not camera up)
        if up != 0:
            self._position.y += up * speed
    
    def zoom(self, delta: float) -> None:
        """
        Zoom the camera in or out (orbit) or change move speed (free).
        
        Args:
            delta: Positive to zoom out, negative to zoom in
        """
        if self.mode == 'orbit':
            if delta > 0:
                self.distance *= self.zoom_speed
            else:
                self.distance /= self.zoom_speed
            
            # Clamp distance
            self.distance = max(self.min_distance, min(self.max_distance, self.distance))
            
            self._update_position()
        else:
            # In free mode, adjust movement speed
            if delta > 0:
                self.move_speed *= 1.2
            else:
                self.move_speed /= 1.2
            
            # Clamp speed
            self.move_speed = max(10.0, min(5000.0, self.move_speed))
    
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
    
    def toggle_mode(self) -> str:
        """
        Toggle between orbit and free camera modes.
        
        Returns:
            The new mode name
        """
        if self.mode == 'orbit':
            self.mode = 'free'
            # Convert orbit position to free position
            # Position stays the same, just change how we control it
            self.yaw = self.azimuth - 180.0  # Face toward target
            self.pitch = -self.elevation
        else:
            self.mode = 'orbit'
            # Convert free position to orbit
            # Calculate distance and angles from current position to target
            diff = self._position - self.target
            self.distance = diff.magnitude
            if self.distance > 0:
                self.elevation = math.degrees(math.asin(diff.y / self.distance))
                self.azimuth = math.degrees(math.atan2(diff.x, diff.z))
        
        self._update_position()
        return self.mode
    
    def reset(self) -> None:
        """Reset the camera to default position."""
        if self.mode == 'orbit':
            self.distance = 500.0
            self.azimuth = 45.0
            self.elevation = 30.0
            self.target = Vector3(0, 0, 0)
        else:
            self._position = Vector3(350, 250, 350)
            self.yaw = -135.0
            self.pitch = -30.0
        self._update_position()
