# Django 2.2 has only *_text, Django 3.2 has both *_text and *_str,
# Django 4.0 has only *_str. These are imported so many places that
# it is better to do it once, hence this file

# When no longer supporting 2.2:
# s/nav.compatibility \(import \w+_str\)/django.utils.encoding \1/
try:
    from django.utils.encoding import force_str
except ImportError:
    from django.utils.encoding import force_text as force_str

try:
    from django.utils.encoding import smart_str
except ImportError:
    from django.utils.encoding import smart_text as smart_str

# lru_cache isn't used that much but one application of sed is faster
# than changing a block into a line three times.

# When no longer supporting 2.2:
# s/nav.compatibility import lru_cache/functools import lru_cache/
try:
    from functools import lru_cache
except ImportError:
    from django.utils.lru_cache import lru_cache
