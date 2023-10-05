from collections import OrderedDict

from rest_framework.authentication import SessionAuthentication
from wagtail import VERSION as WAGTAIL_VERSION
from wagtail.admin.navigation import get_explorable_root_page
from wagtail.models import Page, UserPagePermissionsProxy

if WAGTAIL_VERSION >= (5, 1):
    from wagtail.permission_policies.pages import PagePermissionPolicy

from ..wagtail_api_v2.views import PagesAPIViewSet
from .filters import ForExplorerFilter, HasChildrenFilter
from .serializers import AdminPageSerializer


class PagesAdminAPIViewSet(PagesAPIViewSet):
    base_serializer_class = AdminPageSerializer
    authentication_classes = [SessionAuthentication]

    # Add has_children filter
    filter_backends = PagesAPIViewSet.filter_backends + [
        HasChildrenFilter,
    ]

    meta_fields = PagesAPIViewSet.meta_fields + [
        'latest_revision_created_at',
        'status',
        'children',
        'descendants',
        'parent',
        'ancestors',
    ]

    body_fields = PagesAPIViewSet.body_fields + [
        'admin_display_title',
    ]

    listing_default_fields = PagesAPIViewSet.listing_default_fields + [
        'latest_revision_created_at',
        'status',
        'children',
        'admin_display_title',
    ]

    # Allow the parent field to appear on listings
    detail_only_fields = []

    known_query_parameters = PagesAPIViewSet.known_query_parameters.union([
        'has_children'
    ])

    def get_root_page(self):
        """
        Returns the page that is used when the `&child_of=root` filter is used.
        """
        return Page.get_first_root_node()

    def get_base_queryset(self):
        """
        Returns a queryset containing all pages that can be seen by this user.

        This is used as the base for get_queryset and is also used to find the
        parent pages when using the child_of and descendant_of filters as well.
        """
        return Page.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()

        # Hide root page
        # TODO: Add "include_root" flag
        # .specific() is required to use .get_admin_display_title()
        queryset = queryset.exclude(depth=1).specific()
        return queryset

    def get_type_info(self):
        types = OrderedDict()

        for name, model in self.seen_types.items():
            types[name] = OrderedDict([
                ('verbose_name', model._meta.verbose_name),
                ('verbose_name_plural', model._meta.verbose_name_plural),
            ])

        return types

    def listing_view(self, request):
        response = super().listing_view(request)
        response.data['__types'] = self.get_type_info()
        return response

    def detail_view(self, request, pk):
        response = super().detail_view(request, pk)
        response.data['__types'] = self.get_type_info()
        return response


class PagesForExplorerAdminAPIViewSet(PagesAdminAPIViewSet):
    # Add for_explorer filter
    filter_backends = PagesAPIViewSet.filter_backends + [
        ForExplorerFilter,
    ]

    def get_root_page(self):
        if WAGTAIL_VERSION >= (5, 1):
            return PagePermissionPolicy().explorable_root_instance(self.request.user)
        return get_explorable_root_page(self.request.user)

    def get_base_queryset(self, models=None):
        queryset = super().get_base_queryset(models=models)

        if WAGTAIL_VERSION >= (5, 1):
            permission_policy = PagePermissionPolicy()
            queryset = queryset & permission_policy.explorable_instances(self.request.user)
        else:
            user_perms = UserPagePermissionsProxy(self.request.user)
            queryset = queryset & user_perms.explorable_pages()

        return queryset
