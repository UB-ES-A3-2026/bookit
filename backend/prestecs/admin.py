from django.contrib import admin

from prestecs.models import Comanda, LiniaComanda


class LiniaComandaInline(admin.TabularInline):
    model = LiniaComanda
    extra = 0


@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuari", "biblioteca", "estat", "data_lliurament", "creada")
    list_filter = ("estat",)
    inlines = [LiniaComandaInline]
