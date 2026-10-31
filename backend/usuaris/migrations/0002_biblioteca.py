from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("usuaris", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Biblioteca",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=150)),
                (
                    "usuari",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="biblioteca",
                        to="usuaris.usuari",
                    ),
                ),
            ],
        ),
    ]
