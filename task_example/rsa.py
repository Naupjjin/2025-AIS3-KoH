import random
import math

def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    r = int(n ** 0.5) + 1
    for i in range(3, r, 2):
        if n % i == 0:
            return False
    return True

def gen_prime(low=1000, high=50000):
    while True:
        n = random.randint(low, high)
        if is_prime(n):
            return n

def egcd(a, b):
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)

def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        return None
    return x % m

def rsa_gen():

    p = gen_prime()
    q = gen_prime()
    n = p * q
    if n > 2**32 - 1:
        return rsa_gen() 

    phi = (p - 1) * (q - 1)

    e = 65537  
    if math.gcd(e, phi) != 1:
        return rsa_gen()
    d = modinv(e, phi)

    m = random.randint(2, n-1)

    c = pow(m, e, n)

    m2 = pow(c, d ,n)
    if m2 != m:
        return rsa_gen

    return (p, q, e, c, m)

rsa_list = rsa_gen()
print([rsa_list[0], rsa_list[1], rsa_list[2], rsa_list[3]])
print([rsa_list[4]])