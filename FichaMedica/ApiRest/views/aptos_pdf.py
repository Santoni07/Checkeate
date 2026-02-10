from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from persona.models import Jugador
from aptos_generales.models import AptoGeneral
from weasyprint import HTML


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def apto_general_pdf(request, id):
    try:
        jugador = Jugador.objects.get(persona__user=request.user)
    except Jugador.DoesNotExist:
        return HttpResponse("Jugador no encontrado", status=404)

    try:
        apto = AptoGeneral.objects.select_related(
            "actividad",
            "medico",
        ).get(id=id, jugador=jugador)
    except AptoGeneral.DoesNotExist:
        return HttpResponse("Apto no encontrado", status=404)

    html_string = render_to_string(
        "medico/ficha_apto_general.html",
        {
            "apto": apto,
            "jugador": jugador,
        }
    )

    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="apto_general_{apto.id}.pdf"'
    return response