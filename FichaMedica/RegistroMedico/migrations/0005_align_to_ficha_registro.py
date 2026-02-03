from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('RegistroMedico', '0002_registromedico_competencia_and_more'),
    ]

    operations = [
        # ⚠️ Solo actualizamos el ESTADO de Django:
        # - decimos que el modelo usa la tabla real 'ficha_registro'
        # - NO ejecutamos SQL de renombrado (porque la tabla ya se llama así)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterModelTable(
                    name='registromedico',
                    table='ficha_registro',
                ),
            ],
            database_operations=[],
        ),
    ]