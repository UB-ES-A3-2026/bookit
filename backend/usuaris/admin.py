from django.contrib import admin, messages

from usuaris.models import PerfilRepartidor


class FiltreEstat(admin.SimpleListFilter):
    """Filtra per estat i, si no se'n tria cap, mostra només els pendents."""

    title = "estat"
    parameter_name = "estat"
    TOTS = "tots"

    def lookups(self, request, model_admin):
        return [*PerfilRepartidor.Estat.choices, (self.TOTS, "Tots")]

    def value(self):
        return super().value() or PerfilRepartidor.Estat.PENDENT

    def queryset(self, request, queryset):
        if self.value() == self.TOTS:
            return queryset
        return queryset.filter(estat=self.value())

    def choices(self, changelist):
        opcions = super().choices(changelist)
        next(opcions)  # L'opció «Tot» de Django no filtraria: la substitueix TOTS.
        yield from opcions


@admin.register(PerfilRepartidor)
class PerfilRepartidorAdmin(admin.ModelAdmin):
    list_display = ["usuari", "cognoms", "dni", "telefon", "vehicle", "estat"]
    list_filter = [FiltreEstat]
    list_select_related = ["usuari"]
    search_fields = ["usuari__name", "usuari__email", "cognoms", "dni"]
    actions = ["validar", "rebutjar"]

    @admin.action(description="Validar", permissions=["change"])
    def validar(self, request, queryset):
        self._resol_pendents(request, queryset, PerfilRepartidor.Estat.VALIDAT)

    @admin.action(description="Rebutjar", permissions=["change"])
    def rebutjar(self, request, queryset):
        self._resol_pendents(request, queryset, PerfilRepartidor.Estat.REBUTJAT)

    def _resol_pendents(self, request, queryset, estat):
        """Canvia l'estat dels pendents i deixa intactes els ja resolts."""
        seleccionats = queryset.count()
        canviats = queryset.filter(estat=PerfilRepartidor.Estat.PENDENT).update(
            estat=estat
        )
        self.message_user(
            request,
            f"Repartidors canviats a «{estat.label}»: {canviats}.",
            messages.SUCCESS,
        )
        if canviats < seleccionats:
            self.message_user(
                request,
                f"Repartidors omesos perquè no estaven pendents: "
                f"{seleccionats - canviats}.",
                messages.WARNING,
            )
