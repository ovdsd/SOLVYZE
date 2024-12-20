import random
import math
import json 

def isprime(number):
    if number < 2:
        return False
    for i in range(2, int(math.sqrt(number)) + 1):
        if number % i == 0:
            return False
    return True

def gen_prime(min, max):
    prime = random.randint(min, max)
    while not isprime(prime):
        prime = random.randint(min, max)
    return prime

def mod_inv(e, phi):
    d, x1, x2, y1 = 0, 0, 1, 1
    temp_phi = phi

    while e > 0:
        temp1 = temp_phi // e
        temp2 = temp_phi - temp1 * e
        temp_phi, e = e, temp2
        x, y = x2 - temp1 * x1, d - temp1 * y1
        x2, x1, d, y1 = x1, x, y1, y

    if temp_phi == 1:
        return d + phi
    raise ValueError("Modular inverse does not exist.")

def generate_rsa_keys():
    p = gen_prime(1000, 5000)
    q = gen_prime(1000, 5000)
    while p == q:
        q = gen_prime(1000, 5000)

    n = p * q
    phi_n = (p - 1) * (q - 1)

    e = random.randint(3, phi_n - 1)
    while math.gcd(e, phi_n) != 1:
        e = random.randint(3, phi_n - 1)

    d = mod_inv(e, phi_n)

    return (e, n), (d, n)

def encrypt_with_public_key(message, e, n):
    encrypted = [pow(ord(char), e, n) for char in message]
    return json.dumps(encrypted)

def decrypt_with_private_key(encrypted_list, d, n):
    return "".join(chr(pow(char, d, n)) for char in encrypted_list)



# def encrypt_with_public_key(message, e, n):
#     return [pow(ord(char), e, n) for char in message]

# def decrypt_with_private_key(encrypted_message, d, n):
#     return "".join(chr(pow(char, d, n)) for char in encrypted_message)