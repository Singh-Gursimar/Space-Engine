"""Physics engine for N-body gravitational simulation with collisions."""

import math
import random
from typing import List, Optional, Tuple, Callable
from .celestial_body import CelestialBody
from .vector3 import Vector3
from .particles import ParticleSystem


class CollisionEvent:
    """Represents a collision between two bodies."""
    
    def __init__(self, body1: CelestialBody, body2: CelestialBody, 
                 impact_velocity: float, position: Vector3):
        self.body1 = body1
        self.body2 = body2
        self.impact_velocity = impact_velocity
        self.position = position
        self.collision_type = "merge"  # merge, explosion, fragment, black_hole_consume
        
        # Check for black holes or neutron stars
        body1_is_black_hole = 'black hole' in body1.name.lower()
        body2_is_black_hole = 'black hole' in body2.name.lower()
        body1_is_neutron = 'neutron' in body1.name.lower()
        body2_is_neutron = 'neutron' in body2.name.lower()
        
        # Black holes consume everything (except other black holes)
        if body1_is_black_hole and not body2_is_black_hole:
            self.collision_type = "black_hole_consume"
            return
        elif body2_is_black_hole and not body1_is_black_hole:
            self.collision_type = "black_hole_consume"
            return
        elif body1_is_black_hole and body2_is_black_hole:
            # Two black holes merge
            self.collision_type = "black_hole_merge"
            return
        
        # Neutron stars are extremely dense - they consume smaller objects
        # But if the object is comparable in mass, they merge normally
        if body1_is_neutron and not body2.is_star and body2.mass < body1.mass * 0.5:
            self.collision_type = "neutron_consume"
            return
        elif body2_is_neutron and not body1.is_star and body1.mass < body2.mass * 0.5:
            self.collision_type = "neutron_consume"
            return
        elif body1_is_neutron or body2_is_neutron:
            # Neutron star with comparable mass object - regular merge
            self.collision_type = "merge"
            return
        
        # Regular stars merge with other bodies (don't explode or fragment)
        if (body1.is_star and not body1_is_neutron) or (body2.is_star and not body2_is_neutron):
            self.collision_type = "merge"
            return
        
        # Determine collision type based on impact velocity and mass ratio
        mass_ratio = max(body1.mass, body2.mass) / max(0.001, min(body1.mass, body2.mass))
        
        if impact_velocity > 50:  # High speed impact
            self.collision_type = "explosion"
        elif impact_velocity > 20 and mass_ratio < 5:
            self.collision_type = "fragment"
        else:
            self.collision_type = "merge"


class PhysicsEngine:
    """
    N-body gravitational physics simulation engine with collision detection.
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
        
        # Particle system for effects
        self.particles = ParticleSystem(max_particles=10000)
        
        # Collision settings
        self.collisions_enabled = True
        self.collision_callback: Optional[Callable[[CollisionEvent], None]] = None
        
        # Bodies to add/remove after update (to avoid modifying list during iteration)
        self._bodies_to_add: List[CelestialBody] = []
        self._bodies_to_remove: List[CelestialBody] = []
        
        # Statistics
        self.collision_count = 0
        
        # Physics settings
        self.base_substeps = 8  # Base number of sub-steps per frame (increased for better stability)
        self.min_softening = 0.1  # Very small softening - only prevents true singularities
        self.max_substep_dt = 0.02  # Maximum dt per substep for stability
    
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
        self.particles.clear()
        self._bodies_to_add.clear()
        self._bodies_to_remove.clear()
    
    def compute_gravitational_forces(self) -> None:
        """
        Compute gravitational forces between all pairs of bodies.
        Uses Newton's law of universal gravitation with adaptive softening.
        """
        n = len(self.bodies)
        G = CelestialBody.G
        
        # Reset all accelerations
        for body in self.bodies:
            body.reset_acceleration()
        
        # Compute pairwise gravitational forces
        for i in range(n):
            for j in range(i + 1, n):
                body_i = self.bodies[i]
                body_j = self.bodies[j]
                
                # Direction from i to j
                direction = body_j.position - body_i.position
                distance = direction.magnitude
                
                # Skip if bodies are overlapping (collision will handle this)
                min_dist = (body_i.radius + body_j.radius) * 0.5
                softening = max(self.min_softening, min_dist * 0.1)
                
                if distance < min_dist:
                    continue
                
                # Add small softening to prevent numerical issues
                softened_dist = max(distance, softening)
                
                # Force magnitude: F = G * m1 * m2 / r^2
                force_magnitude = G * body_i.mass * body_j.mass / (softened_dist * softened_dist)
                
                # Force vector (normalized direction * magnitude)
                if distance > 0:
                    force = direction * (force_magnitude / distance)
                else:
                    force = Vector3(0, 0, 0)
                
                # Apply force to body_i (toward body_j)
                body_i.apply_force(force)
                
                # Apply equal and opposite force to body_j (Newton's 3rd law)
                body_j.apply_force(-force)
    
    def detect_collisions(self) -> List[CollisionEvent]:
        """Detect collisions between all pairs of bodies."""
        collisions = []
        n = len(self.bodies)
        
        for i in range(n):
            for j in range(i + 1, n):
                body_i = self.bodies[i]
                body_j = self.bodies[j]
                
                # Skip if either is marked for removal
                if body_i in self._bodies_to_remove or body_j in self._bodies_to_remove:
                    continue
                
                # Calculate distance between centers
                direction = body_j.position - body_i.position
                distance = direction.magnitude
                
                # Check if bodies are overlapping
                collision_distance = body_i.radius + body_j.radius
                
                if distance < collision_distance:
                    # Calculate relative velocity
                    relative_vel = body_j.velocity - body_i.velocity
                    impact_velocity = relative_vel.magnitude
                    
                    # Collision position (weighted by mass)
                    total_mass = body_i.mass + body_j.mass
                    collision_pos = (body_i.position * body_j.mass + 
                                   body_j.position * body_i.mass) / total_mass
                    
                    event = CollisionEvent(body_i, body_j, impact_velocity, collision_pos)
                    collisions.append(event)
        
        return collisions
    
    def handle_collision(self, event: CollisionEvent) -> None:
        """Handle a collision event."""
        # Check if either body has already been processed in another collision this frame
        if event.body1 in self._bodies_to_remove or event.body2 in self._bodies_to_remove:
            return

        body1 = event.body1
        body2 = event.body2
        
        # Mark both for removal
        self._bodies_to_remove.append(body1)
        self._bodies_to_remove.append(body2)
        
        self.collision_count += 1
        
        if event.collision_type == "black_hole_consume":
            self._handle_black_hole_consume(event)
        elif event.collision_type == "black_hole_merge":
            self._handle_black_hole_merge(event)
        elif event.collision_type == "neutron_consume":
            self._handle_neutron_consume(event)
        elif event.collision_type == "explosion":
            self._handle_explosion(event)
        elif event.collision_type == "fragment":
            self._handle_fragmentation(event)
        else:
            self._handle_merge(event)
        
        # Call callback if set
        if self.collision_callback:
            self.collision_callback(event)
    
    def _handle_black_hole_consume(self, event: CollisionEvent) -> None:
        """Handle a black hole consuming an object."""
        body1, body2 = event.body1, event.body2
        
        # Determine which is the black hole
        black_hole = body1 if 'black hole' in body1.name.lower() else body2
        consumed = body2 if black_hole == body1 else body1
        
        # Black hole grows in mass but not much in size
        new_mass = black_hole.mass + consumed.mass
        # Schwarzschild radius: r ∝ mass, but we'll grow it slowly
        new_radius = black_hole.radius * (1 + 0.05 * (consumed.mass / black_hole.mass))
        
        # Conservation of momentum
        new_velocity = (black_hole.velocity * black_hole.mass + consumed.velocity * consumed.mass) / new_mass
        
        # Create enhanced black hole
        enhanced_black_hole = CelestialBody(
            name=black_hole.name,
            mass=new_mass,
            radius=new_radius,
            position=black_hole.position,
            velocity=new_velocity,
            color=(0.05, 0.0, 0.1),  # Very dark purple
            is_star=True
        )
        
        self._bodies_to_add.append(enhanced_black_hole)
        
        # Create accretion disk effect
        self.particles.create_debris(
            black_hole.position,
            new_velocity,
            (0.8, 0.4, 1.0),  # Purple glow
            num_particles=80,
            spread=30.0,
            size=3.0
        )
        
        print(f"Black hole consumed {consumed.name}! New mass: {new_mass:.0f}")
    
    def _handle_black_hole_merge(self, event: CollisionEvent) -> None:
        """Handle two black holes merging (gravitational wave event)."""
        body1, body2 = event.body1, event.body2
        
        total_mass = body1.mass + body2.mass
        new_velocity = (body1.velocity * body1.mass + body2.velocity * body2.mass) / total_mass
        
        # Merged black hole is larger
        new_radius = max(body1.radius, body2.radius) * 1.4
        
        merged_black_hole = CelestialBody(
            name="Supermassive Black Hole",
            mass=total_mass * 0.95,  # Small amount of mass radiated as gravitational waves
            radius=new_radius,
            position=event.position,
            velocity=new_velocity,
            color=(0.02, 0.0, 0.05),  # Almost black
            is_star=True
        )
        
        self._bodies_to_add.append(merged_black_hole)
        
        # Massive gravitational wave burst (visual effect)
        for i in range(4):
            self.particles.create_shockwave(
                event.position,
                (0.5, 0.2, 0.8),
                radius=150.0 + i * 50,
                num_particles=100
            )
        
        print(f"BLACK HOLE MERGER! Gravitational waves detected! Mass: {merged_black_hole.mass:.0f}")
    
    def _handle_neutron_consume(self, event: CollisionEvent) -> None:
        """Handle a neutron star consuming a smaller object."""
        body1, body2 = event.body1, event.body2
        
        # Determine which is the neutron star
        neutron = body1 if 'neutron' in body1.name.lower() else body2
        consumed = body2 if neutron == body1 else body1
        
        new_mass = neutron.mass + consumed.mass
        # Neutron stars stay very compact
        new_radius = neutron.radius * (1 + 0.02 * (consumed.mass / neutron.mass))
        
        new_velocity = (neutron.velocity * neutron.mass + consumed.velocity * consumed.mass) / new_mass
        
        enhanced_neutron = CelestialBody(
            name=neutron.name,
            mass=new_mass,
            radius=new_radius,
            position=neutron.position,
            velocity=new_velocity,
            color=(0.8, 0.95, 1.0),  # Bright blue-white
            is_star=True
        )
        
        self._bodies_to_add.append(enhanced_neutron)
        
        # X-ray burst effect
        self.particles.create_explosion(
            neutron.position,
            (0.7, 0.9, 1.0),
            num_particles=60,
            speed=80.0,
            size=3.0,
            lifetime=1.5
        )
        
        print(f"Neutron star consumed {consumed.name}! Mass: {new_mass:.0f}")
    
    def _handle_merge(self, event: CollisionEvent) -> None:
        """Handle a merger collision - two bodies become one."""
        body1, body2 = event.body1, event.body2
        
        # Conservation of momentum
        total_mass = body1.mass + body2.mass
        new_velocity = (body1.velocity * body1.mass + body2.velocity * body2.mass) / total_mass
        
        # New position (center of mass)
        new_position = event.position
        
        # New radius (volume addition)
        new_volume = (4/3) * math.pi * (body1.radius**3 + body2.radius**3)
        new_radius = (new_volume * 3 / (4 * math.pi)) ** (1/3)
        
        # Blend colors based on mass
        r = (body1.color[0] * body1.mass + body2.color[0] * body2.mass) / total_mass
        g = (body1.color[1] * body1.mass + body2.color[1] * body2.mass) / total_mass
        b = (body1.color[2] * body1.mass + body2.color[2] * body2.mass) / total_mass
        new_color = (min(1.0, r), min(1.0, g), min(1.0, b))
        
        # Check if either body is already a black hole or neutron star (shouldn't happen here but safety check)
        body1_is_exotic = 'black hole' in body1.name.lower() or 'neutron' in body1.name.lower()
        body2_is_exotic = 'black hole' in body2.name.lower() or 'neutron' in body2.name.lower()
        
        # Determine if result is a star
        is_star = body1.is_star or body2.is_star
        
        # Check for SUPERNOVA - when merged star exceeds critical mass
        # But only for regular stars, not already exotic objects
        SUPERNOVA_MASS_THRESHOLD = 4000.0
        BLACK_HOLE_MASS_THRESHOLD = 6000.0
        
        if is_star and not body1_is_exotic and not body2_is_exotic and total_mass > SUPERNOVA_MASS_THRESHOLD:
            self._handle_supernova(event, total_mass, new_position, new_velocity)
            return
        
        # Create merged body
        larger = body1 if body1.mass > body2.mass else body2
        merged = CelestialBody(
            name=f"{larger.name}+",
            mass=total_mass,
            radius=new_radius,
            position=new_position,
            velocity=new_velocity,
            color=new_color,
            is_star=is_star
        )
        
        self._bodies_to_add.append(merged)
        
        # Create small merge effect
        self.particles.create_explosion(
            event.position,
            new_color,
            num_particles=30,
            speed=20.0,
            size=2.0,
            lifetime=1.0
        )
    
    def _handle_supernova(self, event: CollisionEvent, total_mass: float, 
                          position: Vector3, velocity: Vector3) -> None:
        """Handle a supernova explosion when star mass exceeds critical threshold."""
        BLACK_HOLE_MASS_THRESHOLD = 6000.0
        
        # Massive explosion effect
        self.particles.create_explosion(
            position,
            (1.0, 0.9, 0.5),  # Bright yellow-white
            num_particles=800,
            speed=150.0,
            size=8.0,
            lifetime=5.0
        )
        
        # Multiple shockwaves
        for i in range(3):
            self.particles.create_shockwave(
                position,
                (1.0, 0.7 - i * 0.2, 0.3),
                radius=100.0 + i * 50,
                num_particles=150
            )
        
        # Create debris cloud
        self.particles.create_debris(
            position,
            velocity,
            (0.8, 0.4, 0.2),
            num_particles=200,
            spread=100.0,
            size=4.0
        )
        
        # Determine remnant type based on mass
        if total_mass > BLACK_HOLE_MASS_THRESHOLD:
            # Create a BLACK HOLE
            remnant = CelestialBody(
                name="Black Hole",
                mass=total_mass * 0.4,  # Some mass ejected
                radius=8,  # Small but massive
                position=position,
                velocity=velocity,
                color=(0.1, 0.0, 0.1),
                is_star=True  # Treated as star for physics
            )
            self._bodies_to_add.append(remnant)
            print(f"SUPERNOVA! Black Hole formed with mass {remnant.mass:.0f}")
        else:
            # Create a NEUTRON STAR
            remnant = CelestialBody(
                name="Neutron Star",
                mass=total_mass * 0.3,  # Most mass ejected
                radius=4,  # Very small
                position=position,
                velocity=velocity,
                color=(0.7, 0.9, 1.0),
                is_star=True
            )
            self._bodies_to_add.append(remnant)
            print(f"SUPERNOVA! Neutron Star formed with mass {remnant.mass:.0f}")
        
        # Eject some planetary nebula fragments
        num_fragments = random.randint(3, 6)
        ejected_mass = total_mass * 0.1 / num_fragments
        
        for i in range(num_fragments):
            angle = 2 * math.pi * i / num_fragments + random.uniform(-0.3, 0.3)
            elevation = random.uniform(-0.5, 0.5)
            
            direction = Vector3(
                math.cos(angle) * math.cos(elevation),
                math.sin(elevation),
                math.sin(angle) * math.cos(elevation)
            )
            
            frag_velocity = velocity + direction * random.uniform(80, 150)
            frag_position = position + direction * 50
            
            fragment = CelestialBody(
                name=f"Nebula_{self.collision_count}_{i}",
                mass=ejected_mass,
                radius=random.uniform(3, 8),
                position=frag_position,
                velocity=frag_velocity,
                color=(random.uniform(0.5, 1.0), random.uniform(0.3, 0.7), random.uniform(0.5, 1.0)),
                is_star=False
            )
            self._bodies_to_add.append(fragment)
    
    def _handle_explosion(self, event: CollisionEvent) -> None:
        """Handle a high-energy collision - bodies are destroyed."""
        body1, body2 = event.body1, event.body2
        
        # Calculate explosion energy
        total_mass = body1.mass + body2.mass
        combined_velocity = (body1.velocity + body2.velocity) * 0.5
        
        # Blend colors for explosion
        avg_color = (
            (body1.color[0] + body2.color[0]) / 2,
            (body1.color[1] + body2.color[1]) / 2,
            (body1.color[2] + body2.color[2]) / 2
        )
        
        # Create massive explosion
        explosion_size = (body1.radius + body2.radius) * 2
        num_particles = int(min(500, total_mass * 50))
        
        self.particles.create_explosion(
            event.position,
            (1.0, 0.8, 0.3),  # Bright yellow-orange
            num_particles=num_particles,
            speed=event.impact_velocity * 2,
            size=explosion_size * 0.1,
            lifetime=3.0
        )
        
        # Create shockwave
        self.particles.create_shockwave(
            event.position,
            (1.0, 0.5, 0.2),
            radius=explosion_size * 3,
            num_particles=80
        )
        
        # Create debris
        self.particles.create_debris(
            event.position,
            combined_velocity,
            avg_color,
            num_particles=num_particles // 2,
            spread=event.impact_velocity,
            size=3.0
        )
        
        # Maybe create some small fragments
        num_fragments = random.randint(2, 5)
        fragment_mass = total_mass * 0.05  # Each fragment is 5% of total
        
        for i in range(num_fragments):
            if fragment_mass < 0.001:
                break
                
            # Random direction
            angle = random.uniform(0, 2 * math.pi)
            elevation = random.uniform(-0.5, 0.5)
            
            direction = Vector3(
                math.cos(angle) * math.cos(elevation),
                math.sin(elevation),
                math.sin(angle) * math.cos(elevation)
            )
            
            frag_velocity = combined_velocity + direction * event.impact_velocity * 0.5
            frag_position = event.position + direction * (body1.radius + body2.radius)
            
            fragment = CelestialBody(
                name=f"Fragment_{self.collision_count}_{i}",
                mass=fragment_mass,
                radius=max(1.0, (body1.radius + body2.radius) * 0.1),
                position=frag_position,
                velocity=frag_velocity,
                color=avg_color,
                is_star=False
            )
            self._bodies_to_add.append(fragment)
    
    def _handle_fragmentation(self, event: CollisionEvent) -> None:
        """Handle a medium-energy collision - bodies fragment."""
        body1, body2 = event.body1, event.body2
        
        total_mass = body1.mass + body2.mass
        combined_velocity = (body1.velocity * body1.mass + body2.velocity * body2.mass) / total_mass
        
        # Create a smaller merged core
        core_mass = total_mass * 0.6
        core_radius = ((body1.radius**3 + body2.radius**3) * 0.6) ** (1/3)
        
        # Blend colors
        avg_color = (
            (body1.color[0] + body2.color[0]) / 2,
            (body1.color[1] + body2.color[1]) / 2,
            (body1.color[2] + body2.color[2]) / 2
        )
        
        larger = body1 if body1.mass > body2.mass else body2
        core = CelestialBody(
            name=f"{larger.name}*",
            mass=core_mass,
            radius=core_radius,
            position=event.position,
            velocity=combined_velocity,
            color=avg_color,
            is_star=body1.is_star or body2.is_star
        )
        self._bodies_to_add.append(core)
        
        # Create fragments
        remaining_mass = total_mass - core_mass
        num_fragments = random.randint(3, 7)
        frag_mass = remaining_mass / num_fragments
        
        for i in range(num_fragments):
            angle = (2 * math.pi * i / num_fragments) + random.uniform(-0.3, 0.3)
            elevation = random.uniform(-0.3, 0.3)
            
            direction = Vector3(
                math.cos(angle) * math.cos(elevation),
                math.sin(elevation),
                math.sin(angle) * math.cos(elevation)
            )
            
            eject_speed = event.impact_velocity * random.uniform(0.3, 0.7)
            frag_velocity = combined_velocity + direction * eject_speed
            frag_position = event.position + direction * (core_radius + 5)
            
            frag_radius = max(1.0, core_radius * 0.3 * random.uniform(0.5, 1.5))
            
            fragment = CelestialBody(
                name=f"Fragment_{self.collision_count}_{i}",
                mass=frag_mass * random.uniform(0.5, 1.5),
                radius=frag_radius,
                position=frag_position,
                velocity=frag_velocity,
                color=(
                    avg_color[0] * random.uniform(0.8, 1.0),
                    avg_color[1] * random.uniform(0.8, 1.0),
                    avg_color[2] * random.uniform(0.8, 1.0)
                ),
                is_star=False
            )
            self._bodies_to_add.append(fragment)
        
        # Create visual effect
        self.particles.create_explosion(
            event.position,
            (1.0, 0.6, 0.2),
            num_particles=100,
            speed=event.impact_velocity,
            size=3.0,
            lifetime=2.0
        )
        
        self.particles.create_debris(
            event.position,
            combined_velocity,
            avg_color,
            num_particles=50,
            spread=event.impact_velocity * 0.5
        )
    
    def _apply_pending_changes(self) -> None:
        """Apply pending body additions and removals."""
        # Remove bodies
        for body in self._bodies_to_remove:
            if body in self.bodies:
                self.bodies.remove(body)
        self._bodies_to_remove.clear()
        
        # Add new bodies
        for body in self._bodies_to_add:
            self.bodies.append(body)
        self._bodies_to_add.clear()
    
    def update(self, dt: float) -> None:
        """
        Update the simulation by one time step using sub-stepping for stability.
        
        Args:
            dt: Time step in seconds
        """
        if self.paused:
            # Still update particles when paused for visual effect
            self.particles.update(dt)
            return
        
        # Apply time scale
        scaled_dt = dt * self.time_scale
        self.total_time += scaled_dt
        
        # Adaptive sub-stepping for stability at high time scales
        # Increase substeps when time scale is high to keep individual steps small
        substeps = max(self.base_substeps, int(self.base_substeps * self.time_scale / 2))
        
        # Ensure individual timestep doesn't exceed max for stability
        sub_dt = scaled_dt / substeps
        if sub_dt > self.max_substep_dt:
            substeps = int(scaled_dt / self.max_substep_dt) + 1
            sub_dt = scaled_dt / substeps
        
        for _ in range(substeps):
            self._physics_step(sub_dt)
        
        # Detect and handle collisions (once per frame, not per substep)
        if self.collisions_enabled:
            collisions = self.detect_collisions()
            for event in collisions:
                self.handle_collision(event)
            self._apply_pending_changes()
        
        # Update particle effects
        self.particles.update(scaled_dt)
        
        # Create atmospheric entry effects for fast-moving small bodies
        for body in self.bodies:
            if body.velocity.magnitude > 80 and body.radius < 5:
                if random.random() < 0.3:  # 30% chance per frame
                    self.particles.create_fire_trail(
                        body.position,
                        body.velocity,
                        (1.0, 0.5, 0.1)
                    )
    
    def _physics_step(self, dt: float) -> None:
        """
        Perform a single physics integration step using 4th-order Yoshida symplectic integrator.
        This provides much better long-term energy conservation than basic leapfrog.
        
        Args:
            dt: Time step in seconds
        """
        # Yoshida 4th-order coefficients
        w0 = -1.7024143839193153
        w1 = 1.3512071919596578
        c1 = w1 / 2
        c2 = (w0 + w1) / 2
        c3 = c2
        c4 = c1
        d1 = w1
        d2 = w0
        d3 = w1
        
        # Step 1: drift c1*dt
        for body in self.bodies:
            body.position = body.position + body.velocity * (c1 * dt)
        
        # Step 2: kick d1*dt
        self.compute_gravitational_forces()
        for body in self.bodies:
            body.velocity = body.velocity + body.acceleration * (d1 * dt)
        
        # Step 3: drift c2*dt
        for body in self.bodies:
            body.position = body.position + body.velocity * (c2 * dt)
        
        # Step 4: kick d2*dt
        self.compute_gravitational_forces()
        for body in self.bodies:
            body.velocity = body.velocity + body.acceleration * (d2 * dt)
        
        # Step 5: drift c3*dt
        for body in self.bodies:
            body.position = body.position + body.velocity * (c3 * dt)
        
        # Step 6: kick d3*dt
        self.compute_gravitational_forces()
        for body in self.bodies:
            body.velocity = body.velocity + body.acceleration * (d3 * dt)
        
        # Step 7: drift c4*dt
        for body in self.bodies:
            body.position = body.position + body.velocity * (c4 * dt)
            
            # Update trail
            body.trail_update_counter += 1
            if body.trail_update_counter >= body.trail_update_frequency:
                body.trail.append(body.position.copy())
                if len(body.trail) > body.trail_length:
                    body.trail.pop(0)
                body.trail_update_counter = 0
    
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
    
    def toggle_collisions(self) -> bool:
        """Toggle collision detection."""
        self.collisions_enabled = not self.collisions_enabled
        return self.collisions_enabled
