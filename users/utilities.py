from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.deconstruct import deconstructible
import re
import unidecode

def get_tokens_for_user(user):
    refresh_token = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh_token),
        'access': str(refresh_token.access_token),
    }

def extract_names(full_name):
    m = re.search(r'(?:^\s*([A-Za-z]+)\s+([A-Za-z]+)\s*([A-Za-z]+)?\s*$|^\s*([Ё-ө]+)\s+([Ё-ө]+)\s*([Ё-ө]+)?\s*$)', full_name)

    if not m:
        raise ValueError('incorrect full name')

    group_start = 1 if m.group(1) else 4 

    last_name, first_name, middle_name = [m.group(i) for i in range(group_start, group_start + 3)]

    middle_name = middle_name if middle_name else ''

    return last_name, first_name, middle_name

def get_grade(text):
    m = re.search(r'^\s*(1[0-2]|[7-9])\s*([A-Za-z])\s*$', text)

    if not m:
        raise ValueError('incorrect grade')
   
    
    return m.group(1)+m.group(2).upper()

@deconstructible
class SafeFileName:
    def __init__(self, subdir):
        self.subdir = subdir

    def __call__(self, instance, filename):
        safe_name = unidecode.unidecode(filename).replace(" ", "-")
        return f"{self.subdir}/{safe_name}"

def safe_file_name(subdir):
    return lambda instance, filename: f"{subdir}/{unidecode.unidecode(filename).replace(' ', '-')}"


safe_file_name = lambda x: SafeFileName(x)
