from django.contrib import admin, messages

from usuaris.models import Biblioteca, FranjaDisponibilitat, PerfilRepartidor


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


class FranjaDisponibilitatInline(admin.TabularInline):
    model = FranjaDisponibilitat
    extra = 0


@admin.register(PerfilRepartidor)
class PerfilRepartidorAdmin(admin.ModelAdmin):
    list_display = ["usuari", "cognoms", "dni", "telefon", "vehicle", "estat"]
    list_filter = [FiltreEstat]
    list_select_related = ["usuari"]
    search_fields = ["usuari__name", "usuari__email", "cognoms", "dni"]
    actions = ["validar", "rebutjar"]
    inlines = [FranjaDisponibilitatInline]

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


@admin.register(Biblioteca)
class BibliotecaAdmin(admin.ModelAdmin):
    """Adreça i ubicació de les biblioteques (US12-T13).

    Les biblioteques es registren des de l'API. Aquí només s'hi completa
    l'adreça i les coordenades, que fan servir el mapa de la ruta del
    repartidor i la cerca de biblioteques properes.
    """

    list_display = ["nom", "correu", "carrer", "numero_porta", "te_ubicacio"]
    list_select_related = ["usuari"]
    search_fields = ["nom", "usuari__email"]
    readonly_fields = ["correu"]
    fieldsets = [
        (None, {"fields": ["nom", "correu"]}),
        ("Adreça", {"fields": ["carrer", "numero_porta"]}),
        (
            "Ubicació",
            {
                "fields": ["latitud", "longitud"],
                "description": (
                    "Coordenades en graus decimals (per exemple, 41.385064 i "
                    "2.173404). Sense coordenades, les recollides d'aquesta "
                    "biblioteca no surten al mapa de la ruta."
                ),
            },
        ),
    ]

    @admin.display(description="correu electrònic", ordering="usuari__email")
    def correu(self, biblioteca):
        return biblioteca.usuari.email

    @admin.display(description="té ubicació", boolean=True)
    def te_ubicacio(self, biblioteca):
        return biblioteca.latitud is not None and biblioteca.longitud is not None

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
