import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q

class Migration(migrations.Migration):

    dependencies = [
        ("Medico", "0004_medico_direccion"),
        ("RegistroMedico", "0001_initial"),
        ("persona", "0002_competencia_jugadorcompetencia"),
    ]

    operations = [
        # ⚠️ 'competencia_id' ya existe EN BD: registrar solo en el ESTADO de Django
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="registromedico",
                    name="competencia",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="registros_medicos",
                        to="persona.competencia",
                    ),
                ),
            ],
            database_operations=[],
        ),

        # Ajuste de 'estado' (esto suele ser ALTER no destructivo; si ya coincide, será no-op)
        migrations.AlterField(
            model_name="registromedico",
            name="estado",
            field=models.CharField(
                blank=True,
                null=True,
                default="PROCESO",
                max_length=45,
                choices=[
                    ("PENDIENTE", "Pendiente"),
                    ("PROCESO", "En proceso"),
                    ("APROBADA", "Aprobada"),
                    ("RECHAZADA", "Rechazada"),
                    ("VENCIDO", "Vencido"),
                ],
            ),
        ),

        # 'torneo' opcional (si ya lo es, no habrá cambios reales)
        migrations.AlterField(
            model_name="registromedico",
            name="torneo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="registros_medicos",
                to="persona.torneo",
            ),
        ),

        # ⚠️ El CHECK YA EXISTE EN BD: registrar solo en el ESTADO (sin ADD CONSTRAINT)
        migrations.SeparateDatabaseAndState(
            state_operations=[
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
