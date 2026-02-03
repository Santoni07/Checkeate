from django.db import migrations, models
from django.db.models import Q

class Migration(migrations.Migration):

    dependencies = [
        ("Medico", "0004_medico_direccion"),
        ("RegistroMedico", "0003_fix_tablename_lowercase"),
        ("persona", "0002_competencia_jugadorcompetencia"),
    ]

    operations = [
        # ❗ No tocar BD: solo actualizar el ESTADO de Django
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Aseguramos que el modelo apunte a la tabla real
                migrations.AlterModelTable(
                    name="registromedico",
                    table="ficha_registro",
                ),
                # Quitamos y volvemos a registrar el CHECK solo en estado
                migrations.RemoveConstraint(
                    model_name="registromedico",
                    name="rm_torneo_xor_competencia",
                ),
                migrations.AddConstraint(
                    model_name="registromedico",
                    constraint=models.CheckConstraint(
                        name="rm_torneo_xor_competencia",
                        check=Q(
                            Q(torneo__isnull=False, competencia__isnull=True) |
                            Q(torneo__isnull=True,  competencia__isnull=False)
                        ),
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]