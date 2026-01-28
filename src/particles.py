"""Particle system for explosions, debris, and visual effects."""

import math
import random
from typing import List, Tuple, Optional
from .vector3 import Vector3


class Particle:
    """A single particle for visual effects."""
    
    def __init__(
        self,
        position: Vector3,
        velocity: Vector3,
        color: Tuple[float, float, float],
        size: float = 2.0,
        lifetime: float = 3.0,
        fade: bool = True,
        particle_type: str = "debris"
    ):
        self.position = position
        self.velocity = velocity
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.fade = fade
        self.particle_type = particle_type
        self.alive = True
    
    @property
    def alpha(self) -> float:
        """Get the alpha value based on remaining lifetime."""
        if self.fade:
            return max(0, self.lifetime / self.max_lifetime)
        return 1.0
    
    def update(self, dt: float) -> None:
        """Update the particle."""
        if not self.alive:
            return
        
        # Move particle
        self.position = self.position + self.velocity * dt
        
        # Apply drag to slow down
        self.velocity = self.velocity * 0.995
        
        # Decrease lifetime
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False


class ParticleSystem:
    """Manages all particles in the simulation."""
    
    def __init__(self, max_particles: int = 5000):
        self.particles: List[Particle] = []
        self.max_particles = max_particles
    
    def add_particle(self, particle: Particle) -> None:
        """Add a particle to the system."""
        if len(self.particles) < self.max_particles:
            self.particles.append(particle)
    
    def create_explosion(
        self,
        position: Vector3,
        color: Tuple[float, float, float],
        num_particles: int = 50,
        speed: float = 50.0,
        size: float = 3.0,
        lifetime: float = 2.0
    ) -> None:
        """Create an explosion effect at the given position."""
        for _ in range(num_particles):
            if len(self.particles) >= self.max_particles:
                break
            
            # Random direction
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            
            dir_x = math.sin(phi) * math.cos(theta)
            dir_y = math.sin(phi) * math.sin(theta)
            dir_z = math.cos(phi)
            
            direction = Vector3(dir_x, dir_y, dir_z)
            
            # Random speed variation
            particle_speed = speed * random.uniform(0.3, 1.0)
            velocity = direction * particle_speed
            
            # Color variation
            color_var = random.uniform(0.8, 1.2)
            particle_color = (
                min(1.0, color[0] * color_var),
                min(1.0, color[1] * color_var),
                min(1.0, color[2] * color_var)
            )
            
            particle = Particle(
                position=position.copy(),
                velocity=velocity,
                color=particle_color,
                size=size * random.uniform(0.5, 1.5),
                lifetime=lifetime * random.uniform(0.5, 1.5),
                particle_type="explosion"
            )
            self.particles.append(particle)
    
    def create_debris(
        self,
        position: Vector3,
        velocity: Vector3,
        color: Tuple[float, float, float],
        num_particles: int = 30,
        spread: float = 30.0,
        size: float = 2.0
    ) -> None:
        """Create debris particles from a collision."""
        for _ in range(num_particles):
            if len(self.particles) >= self.max_particles:
                break
            
            # Random offset direction
            offset = Vector3(
                random.uniform(-1, 1),
                random.uniform(-1, 1),
                random.uniform(-1, 1)
            ).normalize() * spread
            
            # Inherit some of the original velocity
            particle_vel = velocity * random.uniform(0.2, 0.8) + offset
            
            particle = Particle(
                position=position.copy(),
                velocity=particle_vel,
                color=color,
                size=size * random.uniform(0.3, 1.0),
                lifetime=random.uniform(3.0, 8.0),
                particle_type="debris"
            )
            self.particles.append(particle)
    
    def create_shockwave(
        self,
        position: Vector3,
        color: Tuple[float, float, float],
        radius: float = 50.0,
        num_particles: int = 100
    ) -> None:
        """Create a spherical shockwave effect."""
        for _ in range(num_particles):
            if len(self.particles) >= self.max_particles:
                break
            
            # Distribute on sphere surface
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            
            dir_x = math.sin(phi) * math.cos(theta)
            dir_y = math.sin(phi) * math.sin(theta)
            dir_z = math.cos(phi)
            
            direction = Vector3(dir_x, dir_y, dir_z)
            velocity = direction * radius * 2
            
            particle = Particle(
                position=position.copy(),
                velocity=velocity,
                color=color,
                size=4.0,
                lifetime=0.5,
                particle_type="shockwave"
            )
            self.particles.append(particle)
    
    def create_fire_trail(
        self,
        position: Vector3,
        velocity: Vector3,
        color: Tuple[float, float, float] = (1.0, 0.5, 0.1)
    ) -> None:
        """Create a fire/heat trail particle."""
        if len(self.particles) >= self.max_particles:
            return
        
        # Opposite of velocity direction with some spread
        trail_vel = velocity * -0.1 + Vector3(
            random.uniform(-5, 5),
            random.uniform(-5, 5),
            random.uniform(-5, 5)
        )
        
        particle = Particle(
            position=position.copy(),
            velocity=trail_vel,
            color=color,
            size=random.uniform(2, 5),
            lifetime=random.uniform(0.3, 0.8),
            particle_type="fire"
        )
        self.particles.append(particle)
    
    def update(self, dt: float) -> None:
        """Update all particles."""
        # Update particles
        for particle in self.particles:
            particle.update(dt)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.alive]
    
    def clear(self) -> None:
        """Remove all particles."""
        self.particles.clear()
