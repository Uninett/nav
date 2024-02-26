# lru_cache isn't used that much but one application of sed is faster
# than changing a block into a line three times.

# When no longer supporting 2.2:
# s/nav.compatibility import lru_cache/functools import lru_cache/
try:
    from functools import lru_cache
except ImportError:
    from django.utils.lru_cache import lru_cache
