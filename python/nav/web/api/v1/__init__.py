from rest_framework import pagination


class NavPageNumberPagination(pagination.PageNumberPagination):
    """Custom pagination class for NAV API

    See http://www.django-rest-framework.org/api-guide/pagination/
    """

    page_size = 100
    page_size_query_param = 'page_size'
