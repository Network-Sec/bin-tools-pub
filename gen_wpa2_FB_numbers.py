#!/usr/bin/env python3

# Modern F!B routers by default have long numbers as WPA keys
# These are hard to tackle, even with modern GPUs. Someone
# noticed that within these default keys, no 3 consecutive
# digits are the same, so here's at least a valid shot at it. 
# It generates numbers comprised of 8,12,16,20 digits up till
# a file size of 10 Gigabytes - you can adjust that on the bottom. 

#!/usr/bin/env python3

# Modern F!B routers by default have long numbers as WPA keys
# These are hard to tackle, even with modern GPUs. Someone
# noticed that within these default keys, no 3 consecutive
# digits are the same, so here's at least a valid shot at it. 
# It generates numbers comprised of 8,12,16,20 digits up till
# a file size of 10 Gigabytes - you can adjust that on the bottom. 

import random
import time

def is_valid_number(number):
    """Check if the number has no three consecutive identical digits."""
    return all(number[i] != number[i+1] or number[i] != number[i+2] for i in range(len(number)-2))

def generate_number(length):
    """Generate a number of given length where no three consecutive digits are alike."""
    while True:
        number = [str(random.randint(0, 9)) for _ in range(length)]
        if is_valid_number(number):
            return ''.join(number)

def generate_and_write_numbers(target_size_bytes):
    lengths = [8, 12, 16, 20]
    bytes_per_length = [9, 13, 17, 21]
    total_bytes_per_set = sum(bytes_per_length)
    numbers_per_length = target_size_bytes // total_bytes_per_set

    with open("generated_numbers.txt", "w") as file:
        for length in lengths:
            seen_numbers = set()
            written_count = 0
            last_update_time = time.time()

            while written_count * (length + 1) < numbers_per_length * (length + 1):
                number = generate_number(length)
                if number not in seen_numbers:
                    seen_numbers.add(number)
                    file.write(number + '\n')
                    written_count += 1

                    current_time = time.time()
                    if current_time - last_update_time >= 3:
                        estimated_size = (written_count * (length + 1)) / (1024 ** 3)
                        print(f"Progress for length {length}: {estimated_size:.2f} GB")
                        last_update_time = current_time

# Generate approximately 10GB of numbers
generate_and_write_numbers(10 * 1073741824)
