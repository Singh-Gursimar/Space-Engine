"""3D Vector class for physics calculations."""

import math
import numpy as np


class Vector3:
    """A 3D vector class for physics calculations."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __rmul__(self, scalar: float) -> 'Vector3':
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector3':
        if scalar == 0:
            raise ValueError("Cannot divide by zero")
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)
    
    def __neg__(self) -> 'Vector3':
        return Vector3(-self.x, -self.y, -self.z)
    
    def __repr__(self) -> str:
        return f"Vector3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"
    
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z
    
    @property
    def magnitude(self) -> float:
        """Return the magnitude (length) of the vector."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    @property
    def magnitude_squared(self) -> float:
        """Return the squared magnitude (faster for comparisons)."""
        return self.x**2 + self.y**2 + self.z**2
    
    def normalize(self) -> 'Vector3':
        """Return a unit vector in the same direction."""
        mag = self.magnitude
        if mag == 0:
            return Vector3(0, 0, 0)
        return self / mag
    
    def dot(self, other: 'Vector3') -> float:
        """Return the dot product with another vector."""
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other: 'Vector3') -> 'Vector3':
        """Return the cross product with another vector."""
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def distance_to(self, other: 'Vector3') -> float:
        """Return the distance to another vector."""
        return (self - other).magnitude
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([self.x, self.y, self.z])
    
    @staticmethod
    def from_array(arr: np.ndarray) -> 'Vector3':
        """Create a Vector3 from a numpy array."""
        return Vector3(arr[0], arr[1], arr[2])
    
    def copy(self) -> 'Vector3':
        """Return a copy of this vector."""
        return Vector3(self.x, self.y, self.z)
