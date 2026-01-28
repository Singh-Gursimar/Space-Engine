"""Celestial body class representing planets, stars, moons, etc."""

import math
from typing import Tuple, List, Optional
from .vector3 import Vector3


class CelestialBody:
    """
    Represents a celestial body (star, planet, moon, asteroid, etc.)
    with physical properties and orbital mechanics.
    """
    
    # Gravitational constant (scaled for visual simulation)
    # Using a much larger value to work with smaller masses and distances
    G = 100.0  # Scaled for visual units
    
    def __init__(
        self,
        name: str,
        mass: float,
        radius: float,
        position: Vector3,
        velocity: Vector3,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        is_star: bool = False,
        trail_length: int = 500
    ):
        """
        Initialize a celestial body.
        
        Args:
            name: Name of the body
            mass: Mass in kg
            radius: Radius in meters (scaled for visualization)
            position: Initial position vector
            velocity: Initial velocity vector
            color: RGB color tuple (0-1 range)
            is_star: Whether this body is a star (affects rendering)
            trail_length: Number of trail points to keep
        """
        self.name = name
        self.mass = mass
        self.radius = radius
        self.position = position
        self.velocity = velocity
        self.color = color
        self.is_star = is_star
        
        # Acceleration (computed each frame)
        self.acceleration = Vector3(0, 0, 0)
        
        # Trail for orbital visualization
        self.trail: List[Vector3] = []
        self.trail_length = trail_length
        self.trail_update_counter = 0
        self.trail_update_frequency = 5  # Update trail every N frames
        
        # Selection state
        self.is_selected = False
    
    def apply_force(self, force: Vector3) -> None:
        """Apply a force to this body (F = ma, so a = F/m)."""
        self.acceleration = self.acceleration + (force / self.mass)
    
    def reset_acceleration(self) -> None:
        """Reset acceleration for the next physics step."""
        self.acceleration = Vector3(0, 0, 0)
    
    def update(self, dt: float) -> None:
        """
        Update position and velocity using Velocity Verlet integration.
        
        Args:
            dt: Time step in seconds
        """
        # Update velocity (half step)
        self.velocity = self.velocity + self.acceleration * (dt * 0.5)
        
        # Update position
        self.position = self.position + self.velocity * dt
        
        # Update trail
        self.trail_update_counter += 1
        if self.trail_update_counter >= self.trail_update_frequency:
            self.trail.append(self.position.copy())
            if len(self.trail) > self.trail_length:
                self.trail.pop(0)
            self.trail_update_counter = 0
    
    def update_velocity(self, dt: float) -> None:
        """Complete the velocity update (second half of Verlet)."""
        self.velocity = self.velocity + self.acceleration * (dt * 0.5)
    
    def gravitational_force_from(self, other: 'CelestialBody') -> Vector3:
        """
        Calculate the gravitational force exerted by another body on this one.
        
        Args:
            other: The other celestial body
            
        Returns:
            Force vector pointing toward the other body
        """
        # Direction from self to other
        direction = other.position - self.position
        distance = direction.magnitude
        
        # Avoid division by zero and extreme forces at close range
        min_distance = (self.radius + other.radius) * 0.5
        if distance < min_distance:
            distance = min_distance
        
        # Newton's law of gravitation: F = G * m1 * m2 / r^2
        force_magnitude = self.G * self.mass * other.mass / (distance ** 2)
        
        # Return force vector
        return direction.normalize() * force_magnitude
    
    def kinetic_energy(self) -> float:
        """Calculate kinetic energy: KE = 0.5 * m * v^2"""
        return 0.5 * self.mass * self.velocity.magnitude_squared
    
    def potential_energy_with(self, other: 'CelestialBody') -> float:
        """Calculate gravitational potential energy with another body."""
        distance = self.position.distance_to(other.position)
        if distance == 0:
            return 0
        return -self.G * self.mass * other.mass / distance
    
    def orbital_velocity_for(self, central_mass: float, orbital_radius: float) -> float:
        """
        Calculate the orbital velocity needed for a circular orbit.
        
        Args:
            central_mass: Mass of the central body
            orbital_radius: Desired orbital radius
            
        Returns:
            Required orbital velocity
        """
        return math.sqrt(self.G * central_mass / orbital_radius)
    
    def clear_trail(self) -> None:
        """Clear the orbital trail."""
        self.trail.clear()
    
    def __repr__(self) -> str:
        return f"CelestialBody('{self.name}', mass={self.mass:.2e}, pos={self.position})"
