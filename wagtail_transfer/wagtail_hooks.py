from django.conf import settings
from django.contrib.auth.models import Permission
from django.templatetags.static import static
from django.urls import include, re_path, reverse
from wagtail import hooks, VERSION as WAGTAIL_VERSION
from wagtail.admin.menu import MenuItem

from . import admin_urls


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        re_path(r'^wagtail-transfer/', include(admin_urls, namespace='wagtail_transfer_admin')),
    ]


class WagtailTransferMenuItem(MenuItem):
    def is_shown(self, request):
        return all(
            [
                bool(getattr(settings, "WAGTAILTRANSFER_SOURCES", None)),
                request.user.has_perm("wagtail_transfer.wagtailtransfer_can_import"),
            ]
        )


@hooks.register('register_admin_menu_item')
def register_admin_menu_item():
    if WAGTAIL_VERSION >= (5, 2):
        kwargs = {"classname": "icon icon-doc-empty-inverse"}
    else:
        kwargs = {"classnames": "icon icon-doc-empty-inverse"}

    return WagtailTransferMenuItem(
        'Import',
        reverse('wagtail_transfer_admin:choose_page'),
        order=10000,
        **kwargs
    )


@hooks.register("register_permissions")
def register_wagtail_transfer_permission():
    return Permission.objects.filter(
        content_type__app_label="wagtail_transfer",
        codename="wagtailtransfer_can_import",
    )
