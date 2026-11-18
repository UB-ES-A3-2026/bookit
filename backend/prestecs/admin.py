from django.contrib import admin

from prestecs.models import Comanda, LiniaComanda, Prestec


class LiniaComandaInline(admin.TabularInline):
    model = LiniaComanda
    extra = 0


@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuari", "biblioteca", "estat", "data_lliurament", "creada")
    list_filter = ("estat",)
    inlines = [LiniaComandaInline]


@admin.register(Prestec)
class PrestecAdmin(admin.ModelAdmin):
    list_display = ("llibre", "usuari", "biblioteca", "data_inici", "data_limit", "data_devolucio")
    list_filter = ("biblioteca",)
    search_fields = ("llibre__titol", "usuari__name", "usuari__email")
