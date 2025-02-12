#!/usr/bin/env python3

import random

def generate_cpf():
    # Generate first 9 digits
    cpf = [random.randint(0, 9) for _ in range(9)]
    
    # Calculate first check digit
    total = sum((10 - i) * cpf[i] for i in range(9))
    cpf.append((11 - (total % 11)) % 10)
    
    # Calculate second check digit
    total = sum((11 - i) * cpf[i] for i in range(10))
    cpf.append((11 - (total % 11)) % 10)
    
    return ''.join(map(str, cpf))

def generate_cnpj():
    # Generate first 12 digits
    cnpj = [random.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    
    # Calculate first check digit
    weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(weights[i] * cnpj[i] for i in range(12))
    cnpj.append((11 - (total % 11)) % 10)
    
    # Calculate second check digit
    weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(weights[i] * cnpj[i] for i in range(13))
    cnpj.append((11 - (total % 11)) % 10)
    
    return ''.join(map(str, cnpj))

# Generate and print valid CPF/CNPJ
print("Valid CPF:", generate_cpf())
print("Valid CNPJ:", generate_cnpj())
