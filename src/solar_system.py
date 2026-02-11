"""Pre-built solar system configurations."""

import math
from .celestial_body import CelestialBody
from .vector3 import Vector3
from .physics import PhysicsEngine


# Use simplified mass units where the Sun = 1000
SUN_MASS = 1000.0
PLANET_MASS = 1.0  # Small planets don't affect sun much
GAS_GIANT_MASS = 10.0


def orbital_velocity(central_mass: float, distance: float) -> float:
    """Calculate orbital velocity for a circular orbit."""
    return math.sqrt(CelestialBody.G * central_mass / distance)


def create_solar_system(physics: PhysicsEngine, scale: float = 1.0) -> None:
    """
    Create a simplified solar system with well-spaced orbits.
    
    Args:
        physics: The physics engine to add bodies to
        scale: Scale factor for distances and sizes
    """
    # Sun - central star
    sun = CelestialBody(
        name="Sun",
        mass=SUN_MASS,
        radius=25 * scale,
        position=Vector3(0, 0, 0),
        velocity=Vector3(0, 0, 0),
        color=(1.0, 0.9, 0.0),
        is_star=True
    )
    physics.add_body(sun)
    
    # Mercury
    mercury_dist = 80 * scale
    mercury = CelestialBody(
        name="Mercury",
        mass=PLANET_MASS * 0.06,
        radius=3 * scale,
        position=Vector3(mercury_dist, 0, 0),
        velocity=Vector3(0, 0, orbital_velocity(SUN_MASS, mercury_dist)),
        color=(0.7, 0.7, 0.7)
    )
    physics.add_body(mercury)
    
    # Venus
    venus_dist = 140 * scale
    venus = CelestialBody(
        name="Venus",
        mass=PLANET_MASS * 0.8,
        radius=5 * scale,
        position=Vector3(venus_dist, 0, 0),
        velocity=Vector3(0, 0, orbital_velocity(SUN_MASS, venus_dist)),
        color=(0.9, 0.7, 0.5)
    )
    physics.add_body(venus)
    
    # Earth
    earth_dist = 200 * scale
    earth = CelestialBody(
        name="Earth",
        mass=PLANET_MASS,
        radius=6 * scale,
        position=Vector3(earth_dist, 0, 0),
        velocity=Vector3(0, 0, orbital_velocity(SUN_MASS, earth_dist)),
        color=(0.2, 0.5, 1.0)
    )
    physics.add_body(earth)
    
    # Mars
    mars_dist = 280 * scale
    mars = CelestialBody(
        name="Mars",
        mass=PLANET_MASS * 0.1,
        radius=4 * scale,
        position=Vector3(mars_dist, 0, 0),
        velocity=Vector3(0, 0, orbital_velocity(SUN_MASS, mars_dist)),
        color=(0.8, 0.3, 0.1)
    )
    physics.add_body(mars)
    
    # Jupiter
    jupiter_dist = 420 * scale
    jupiter = CelestialBody(
        name="Jupiter",
        mass=GAS_GIANT_MASS,
        radius=15 * scale,
        position=Vector3(jupiter_dist, 0, 0),
        velocity=Vector3(0, 0, orbital_velocity(SUN_MASS, jupiter_dist)),
        color=(0.8, 0.7, 0.6)
    )
    physics.add_body(jupiter)
    
    # Saturn
    saturn_dist = 580 * scale
    saturn = CelestialBody(
        name="Saturn",
        mass=GAS_GIANT_MASS * 0.5,
        radius=12 * scale,
        position=Vector3(saturn_dist, 0, 0),
        velocity=Vector3(0, 0, orbital_velocity(SUN_MASS, saturn_dist)),
        color=(0.9, 0.8, 0.5)
    )
    physics.add_body(saturn)


def create_binary_star_system(physics: PhysicsEngine, scale: float = 1.0) -> None:
    """
    Create a binary star system with planets.
    
    Args:
        physics: The physics engine to add bodies to
        scale: Scale factor for distances and sizes
    """
    # Two stars orbiting each other around their common center of mass
    mass1 = SUN_MASS * 0.8
    mass2 = mass1 * 0.8
    total_mass = mass1 + mass2
    separation = 240 * scale  # Total separation between stars
    
    # Each star orbits the barycenter at distances proportional to the inverse of their masses
    # r1 * m1 = r2 * m2 and r1 + r2 = separation
    r1 = separation * mass2 / total_mass  # Distance of star1 from barycenter
    r2 = separation * mass1 / total_mass  # Distance of star2 from barycenter
    
    # Orbital velocity for each star: v = sqrt(G * M_other / separation)
    # Actually: v1 = sqrt(G * m2^2 / (m1 + m2) / separation)
    v1 = math.sqrt(CelestialBody.G * mass2 * mass2 / total_mass / separation)
    v2 = math.sqrt(CelestialBody.G * mass1 * mass1 / total_mass / separation)
    
    star1 = CelestialBody(
        name="Star Alpha",
        mass=mass1,
        radius=22 * scale,
        position=Vector3(-r1, 0, 0),
        velocity=Vector3(0, 0, -v1),
        color=(1.0, 0.8, 0.4),
        is_star=True
    )
    physics.add_body(star1)
    
    star2 = CelestialBody(
        name="Star Beta",
        mass=mass2,
        radius=20 * scale,
        position=Vector3(r2, 0, 0),
        velocity=Vector3(0, 0, v2),
        color=(0.8, 0.9, 1.0),
        is_star=True
    )
    physics.add_body(star2)
    
    # Planet orbiting both stars (needs to be far enough out)
    planet_dist = 450 * scale
    total_mass = star1.mass + star2.mass
    planet_vel = math.sqrt(CelestialBody.G * total_mass / planet_dist)
    
    planet = CelestialBody(
        name="Circumbinary Planet",
        mass=PLANET_MASS * 2,
        radius=8 * scale,
        position=Vector3(planet_dist, 0, 0),
        velocity=Vector3(0, 0, planet_vel),
        color=(0.3, 0.8, 0.4)
    )
    physics.add_body(planet)


def create_earth_moon_system(physics: PhysicsEngine, scale: float = 1.0) -> None:
    """
    Create an Earth-Moon system.
    
    Args:
        physics: The physics engine to add bodies to
        scale: Scale factor for distances and sizes
    """
    # Earth (as central body with larger mass for this demo)
    earth_mass = 100.0
    earth = CelestialBody(
        name="Earth",
        mass=earth_mass,
        radius=25 * scale,
        position=Vector3(0, 0, 0),
        velocity=Vector3(0, 0, 0),
        color=(0.2, 0.5, 1.0)
    )
    physics.add_body(earth)
    
    # Moon
    moon_dist = 120 * scale
    moon_vel = math.sqrt(CelestialBody.G * earth_mass / moon_dist)
    
    moon = CelestialBody(
        name="Moon",
        mass=PLANET_MASS * 0.1,
        radius=8 * scale,
        position=Vector3(moon_dist, 0, 0),
        velocity=Vector3(0, 0, moon_vel),
        color=(0.7, 0.7, 0.7)
    )
    physics.add_body(moon)


def create_asteroid_belt(physics: PhysicsEngine, central_mass: float, 
                         inner_radius: float, outer_radius: float,
                         num_asteroids: int = 50, scale: float = 1.0) -> None:
    """
    Create an asteroid belt around a central body.
    
    Args:
        physics: The physics engine to add bodies to
        central_mass: Mass of the central body
        inner_radius: Inner radius of the belt
        outer_radius: Outer radius of the belt
        num_asteroids: Number of asteroids to create
        scale: Scale factor
    """
    import random
    
    for i in range(num_asteroids):
        # Random position in belt
        radius = random.uniform(inner_radius, outer_radius) * scale
        angle = random.uniform(0, 2 * math.pi)
        height = random.uniform(-20, 20) * scale
        
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        
        # Orbital velocity
        vel = math.sqrt(CelestialBody.G * central_mass / radius)
        vx = -vel * math.sin(angle)
        vz = vel * math.cos(angle)
        
        # Add some random variation
        vx += random.uniform(-vel * 0.05, vel * 0.05)
        vz += random.uniform(-vel * 0.05, vel * 0.05)
        
        asteroid = CelestialBody(
            name=f"Asteroid_{i}",
            mass=0.001,  # Use scaled mass consistent with other bodies
            radius=random.uniform(1, 3) * scale,
            position=Vector3(x, height, z),
            velocity=Vector3(vx, 0, vz),
            color=(0.5, 0.5, 0.5),
            trail_length=100
        )
        physics.add_body(asteroid)


def create_random_system(physics: PhysicsEngine, num_bodies: int = 10, scale: float = 1.0) -> None:
    """
    Create a random system of bodies with well-spaced orbits.
    
    Args:
        physics: The physics engine to add bodies to
        num_bodies: Number of bodies to create
        scale: Scale factor
    """
    import random
    
    # Central star
    star = CelestialBody(
        name="Central Star",
        mass=SUN_MASS,
        radius=25 * scale,
        position=Vector3(0, 0, 0),
        velocity=Vector3(0, 0, 0),
        color=(1.0, 0.95, 0.8),
        is_star=True
    )
    physics.add_body(star)
    
    # Random planets
    colors = [
        (0.8, 0.4, 0.2),  # Brown
        (0.3, 0.6, 0.9),  # Blue
        (0.2, 0.8, 0.3),  # Green
        (0.9, 0.7, 0.4),  # Tan
        (0.6, 0.2, 0.6),  # Purple
        (0.9, 0.5, 0.5),  # Pink
        (0.4, 0.8, 0.8),  # Cyan
        (0.8, 0.8, 0.2),  # Yellow
    ]
    
    # Space planets out evenly
    for i in range(num_bodies - 1):
        # Distribute distances more evenly (100 to 500, spaced out)
        base_dist = 100 + (400 * (i + 1) / num_bodies)
        dist = (base_dist + random.uniform(-20, 20)) * scale
        angle = random.uniform(0, 2 * math.pi)
        inclination = random.uniform(-0.05, 0.05)
        
        x = dist * math.cos(angle)
        y = dist * inclination
        z = dist * math.sin(angle)
        
        vel = math.sqrt(CelestialBody.G * SUN_MASS / dist)
        vx = -vel * math.sin(angle)
        vz = vel * math.cos(angle)
        
        planet = CelestialBody(
            name=f"Planet_{i+1}",
            mass=random.uniform(PLANET_MASS * 0.5, GAS_GIANT_MASS),
            radius=random.uniform(4, 10) * scale,
            position=Vector3(x, y, z),
            velocity=Vector3(vx, 0, vz),
            color=random.choice(colors)
        )
        physics.add_body(planet)
