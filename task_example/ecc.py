class Point:
    def __init__(self, x, y, p):
        self.x = x % p
        self.y = y % p
        self.modulus = p

def inv_mod(x, p):
    return pow(x, -1, p)

def addition(p1: Point, p2: Point, a, b):
    p = p1.modulus
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y

    if x1 == x2 and y1 == y2:

        numerator = (3 * x1 * x1 + a) % p
        denominator = (2 * y1) % p
        d = numerator * inv_mod(denominator, p) % p
    else:
 
        numerator = (y2 - y1) % p
        denominator = (x2 - x1) % p
        d = numerator * inv_mod(denominator, p) % p

    x3 = (d*d - x1 - x2) % p
    y3 = (d * (x1 - x3) - y1) % p
    return Point(x3, y3, p)

def elliptic_addition(a, b, p, P_x, P_y, Q_x, Q_y):
    P = Point(P_x, P_y, p)
    Q = Point(Q_x, Q_y, p)
    R = addition(P, Q, a, b)
    return R.x, R.y


a = 497
b = 1768
p = 9739
P_x, P_y = 493, 5564
Q_x, Q_y = 1539, 4742

x3, y3 = elliptic_addition(a, b, p, P_x, P_y, Q_x, Q_y)
print(x3, y3)
