from django.contrib import admin

from prestecs.models import CanviEstat, Comanda, LiniaComanda, Notificacio


class LiniaComandaInline(admin.TabularInline):
    model = LiniaComanda
    extra = 0


class CanviEstatInline(admin.TabularInline):
    model = CanviEstat
    extra = 0
    readonly_fields = ("estat", "moment")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # L'historial només el genera l'aplicació en canviar l'estat.
        return False


@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuari", "biblioteca", "estat", "data_lliurament", "repartidor", "creada")
    list_filter = ("estat",)
    inlines = [LiniaComandaInline, CanviEstatInline]


@admin.register(Notificacio)
class NotificacioAdmin(admin.ModelAdmin):
    list_display = ("usuari", "comanda", "text", "llegida", "creada")
    list_filter = ("llegida",)
    search_fields = ("usuari__name", "usuari__email", "text")
    readonly_fields = ("usuari", "comanda", "text", "creada")
