import random

# y^2 = x^3 + a*x + b (mod p)
p = 9739
a, b = 3, 7

def inv_mod(x, m):
    return pow(x, -1, m)

def is_on_curve(x, y):
    return (y * y - (x * x * x + a * x + b)) % p == 0

def point_add(P, Q):
    x1, y1 = P
    x2, y2 = Q

    if x1 == x2 and (y1 + y2) % p == 0:
        return None  

    if P != Q:
        lam = ((y2 - y1) * inv_mod((x2 - x1) % p, p)) % p
    else:
        if y1 == 0:
            return None 
        lam = ((3 * x1 * x1 + a) * inv_mod((2 * y1) % p, p)) % p

    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)

def random_point():
    while True:
        x = random.randint(0, p - 1)
        rhs = (x**3 + a*x + b) % p
    
        if pow(rhs, (p-1)//2, p) != 1:
            continue  
        for y in range(p):
            if (y*y) % p == rhs:
                return (x, y)

while True:
    P = random_point()
    Q = random_point()
    R = point_add(P, Q)
    if R is not None:
        break

print(f"P = {P}")
print(f"Q = {Q}")
print(f"P + Q = {R}")
