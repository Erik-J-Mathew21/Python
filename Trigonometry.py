import math

def calculate_trig(angle_degrees):
    angle_rad = math.radians(angle_degrees)
    
    print(f"Angle: {angle_degrees}°")
    print(f"sin({angle_degrees}°) = {math.sin(angle_rad):.4f}")
    print(f"cos({angle_degrees}°) = {math.cos(angle_rad):.4f}")
    print(f"tan({angle_degrees}°) = {math.tan(angle_rad):.4f}")
    print()

angles = [0, 30, 45, 60, 90]
for angle in angles:
    calculate_trig(angle)