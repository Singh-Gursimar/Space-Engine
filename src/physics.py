"""Physics engine for N-body gravitational simulation."""

from typing import List
from .celestial_body import CelestialBody
from .vector3 import Vector3


class PhysicsEngine:
    """
    N-body gravitational physics simulation engine.
    Uses Velocity Verlet integration for stable orbital mechanics.
    """
    
    def __init__(self, time_scale: float = 1.0):
        """
        Initialize the physics engine.
        
        Args:
            time_scale: Multiplier for simulation speed
        """
        self.bodies: List[CelestialBody] = []
        self.time_scale = time_scale
        self.paused = False
        self.total_time = 0.0
    
    def add_body(self, body: CelestialBody) -> None:
        """Add a celestial body to the simulation."""
        self.bodies.append(body)
    
    def remove_body(self, body: CelestialBody) -> None:
        """Remove a celestial body from the simulation."""
        if body in self.bodies:
            self.bodies.remove(body)
    
    def clear(self) -> None:
        """Remove all bodies from the simulation."""
        self.bodies.clear()
    
    def compute_gravitational_forces(self) -> None:
        """
        Compute gravitational forces between all pairs of bodies.
        Uses Newton's law of universal gravitation.
        """
        n = len(self.bodies)
        
        # Reset all accelerations
        for body in self.bodies:
            body.reset_acceleration()
        
        # Compute pairwise gravitational forces
        for i in range(n):
            for j in range(i + 1, n):
                body_i = self.bodies[i]
                body_j = self.bodies[j]
                
                # Force on body_i from body_j
                force = body_i.gravitational_force_from(body_j)
                
                # Apply force to body_i (toward body_j)
                body_i.apply_force(force)
                
                # Apply equal and opposite force to body_j (Newton's 3rd law)
                body_j.apply_force(-force)
    
    def update(self, dt: float) -> None:
        """
        Update the simulation by one time step.
        
        Uses Velocity Verlet integration:
        1. Compute forces/accelerations
        2. Update velocities (half step)
        3. Update positions
        4. Compute new forces/accelerations
        5. Update velocities (half step)
        
        Args:
            dt: Time step in seconds
        """
        if self.paused:
            return
        
        # Apply time scale
        dt *= self.time_scale
        self.total_time += dt
        
        # Compute initial accelerations
        self.compute_gravitational_forces()
        
        # Update positions and velocities (first half)
        for body in self.bodies:
            body.update(dt)
        
        # Compute new accelerations
        self.compute_gravitational_forces()
        
        # Complete velocity update (second half)
        for body in self.bodies:
            body.update_velocity(dt)
    
    def total_kinetic_energy(self) -> float:
        """Calculate total kinetic energy of the system."""
        return sum(body.kinetic_energy() for body in self.bodies)
    
    def total_potential_energy(self) -> float:
        """Calculate total gravitational potential energy of the system."""
        total = 0.0
        n = len(self.bodies)
        for i in range(n):
            for j in range(i + 1, n):
                total += self.bodies[i].potential_energy_with(self.bodies[j])
        return total
    
    def total_energy(self) -> float:
        """Calculate total mechanical energy (KE + PE)."""
        return self.total_kinetic_energy() + self.total_potential_energy()
    
    def center_of_mass(self) -> Vector3:
        """Calculate the center of mass of the system."""
        if not self.bodies:
            return Vector3(0, 0, 0)
        
        total_mass = sum(body.mass for body in self.bodies)
        weighted_sum = Vector3(0, 0, 0)
        
        for body in self.bodies:
            weighted_sum = weighted_sum + body.position * body.mass
        
        return weighted_sum / total_mass
    
    def toggle_pause(self) -> bool:
        """Toggle pause state and return new state."""
        self.paused = not self.paused
        return self.paused
    
    def set_time_scale(self, scale: float) -> None:
        """Set the simulation time scale."""
        self.time_scale = max(0.01, min(scale, 100.0))
