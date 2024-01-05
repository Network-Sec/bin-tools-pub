import itertools
import string

# Create a list of uppercase & lowercase chars and digits
# a...a!...a!!...z...z!...z!!...aa...aa!...aa!!...ab...ab!...ab!!
# In the example is only one special char (exclamation mark) but the script uses all common 
# special chars used in passwords. 

# hashcat doesn't provide this unique combination # and erroers when we try to generate such a list with --stdout. 
# .\hashcat.exe -d 2 -i -a 3 -1 ?l?u?d ?1?1?1?1?1 --stdout > UpLowDig5.txt -w 3
# OperationStopped: (:) [], OutOfMemoryException
# There's custom combos like -1 ?l?u?d but the custom charset isn't supported in all modes.
# That's why I created this little tool. Have some disk space and time ready. 

chars_digits = list(string.ascii_letters + string.digits)

special_chars = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '-', '=']

def generate_combinations():
    with open("combinations.txt", "w") as file:
        # Generate combinations for 1 to 6 letter-digit strings
        for r in range(1, 7):
            for combo in itertools.product(chars_digits, repeat=r):
                combo_str = ''.join(combo)
                file.write(combo_str + '\n') 

                for special in special_chars:
                    file.write(combo_str + special + '\n')

                for special_combo in itertools.product(special_chars, repeat=2):
                    file.write(combo_str + ''.join(special_combo) + '\n')


generate_combinations()
