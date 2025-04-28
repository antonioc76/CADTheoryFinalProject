from typing_extensions import Self


class Offset:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


    def add(self, other:Self):
        return Offset(self.x + other.x, self.y + other.y, self.z + other.z)


    def subtract(self, other:Self):
        return Offset(self.x - other.x, self.y - other.y, self.z - other.z)


    def print(self):
        print(f"offset: x: {self.x}, y: {self.y}, z: {self.z}")