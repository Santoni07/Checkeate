
from statistics import mean
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, QueryDict
from django.views import View
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Representante, RepresenteColegio,  RepresentanteActividadGeneral
from RegistroMedico.models import RegistroMedico, EstudiosMedico
from persona.models import Categoria,Equipo,JugadorCategoriaEquipo,CategoriaEquipo,Jugador, ActividadGeneral
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404
from estudiante.models import Estudiante
from account.models import Profile
from datetime import datetime, date
from aptos_generales.models import AptoGeneral, EstudiosAptoGeneral
from django.utils.dateparse import parse_date

from Cus.models import (
    Cus, ExamenFisico, ExamenOdontologico, ExamenCardiovascular,
    ExamenRespiratorio, ExamenOftalmologico, ExamenFonoaudiologico,
    ExamenOsteoarticular, ExamenNeurologico
)

class RepresentanteHomeView(LoginRequiredMixin, View):
    def get(self, request):
        profile_id = request.session.get("user_profile_id")
        profile = get_object_or_404(Profile, id=profile_id)

        representante = Representante.objects.filter(profile=profile).first()
        if not representante:
            return render(request, 'Representante/torneo_home.html', {
                "error": "No se encontró información del representante."
            })

        categorias = Categoria.objects.filter(torneo=representante.torneo)
        equipos = Equipo.objects.filter(categoria_equipos__categoria__in=categorias).distinct()

        # Filtros
        query_dict = QueryDict(mutable=True)
        query_dict.update(request.GET)

        filter_type = query_dict.get('filter_type', None)
        filter_team_list = query_dict.getlist('filter_team')
        filter_team = filter_team_list[0] if filter_team_list else None
        filter_category = query_dict.get('filter_category', None)
        search_query = query_dict.get('search_query', None)
        filter_estado = query_dict.get('filter_estado', None)

        filtros_activos = any([filter_type, search_query, filter_estado])

        jugadores = []

        try:
            if filter_type == 'equipo':
                equipo_id = int(filter_team)
                jugadores = Jugador.objects.filter(
                    jugadorcategoriaequipo__categoria_equipo__equipo_id=equipo_id,
                    jugadorcategoriaequipo__categoria_equipo__categoria__torneo=representante.torneo
                ).distinct()

            elif filter_type == 'categoria':
                if filter_category and filter_category != "Todas":
                    categoria_id = int(filter_category)
                    categoria = get_object_or_404(Categoria, id=categoria_id)
                    equipos = Equipo.objects.filter(categoria_equipos__categoria=categoria).distinct()

                    if filter_team:
                        equipo_id = int(filter_team)
                        jugadores = Jugador.objects.filter(
                            jugadorcategoriaequipo__categoria_equipo__equipo_id=equipo_id,
                            jugadorcategoriaequipo__categoria_equipo__categoria_id=categoria_id,
                            jugadorcategoriaequipo__categoria_equipo__categoria__torneo=representante.torneo
                        ).distinct()
                    else:
                        jugadores = Jugador.objects.filter(
                            jugadorcategoriaequipo__categoria_equipo__categoria_id=categoria_id,
                            jugadorcategoriaequipo__categoria_equipo__categoria__torneo=representante.torneo
                        ).distinct()
                else:
                    jugadores = Jugador.objects.filter(
                        jugadorcategoriaequipo__categoria_equipo__categoria__torneo=representante.torneo
                    ).distinct()

            elif filter_type == 'persona' and search_query:
                jugadores = Jugador.objects.filter(
                    Q(persona__profile__dni__icontains=search_query) |
                    Q(persona__profile__nombre__icontains=search_query) |
                    Q(persona__profile__apellido__icontains=search_query),
                    jugadorcategoriaequipo__categoria_equipo__categoria__torneo=representante.torneo
                ).distinct()

            elif filtros_activos:
                jugadores = Jugador.objects.filter(
                    jugadorcategoriaequipo__categoria_equipo__categoria__torneo=representante.torneo
                ).distinct()
            else:
                jugadores = []  # No mostrar nada si no hay filtros

        except (ValueError, Categoria.DoesNotExist, Equipo.DoesNotExist) as e:
            print("Error procesando los filtros:", e)

        jugadores_info = []
        for jugador in jugadores:
            # Buscar la ficha según filtro de estado
            if not filter_estado:
                # Sin filtro: traer la última ficha médica del torneo
                registro_medico = RegistroMedico.objects.filter(
                    jugador=jugador,
                    torneo=representante.torneo
                ).order_by('-fecha_creacion').first()
            else:
                # Con filtro: traer la última ficha médica con ese estado
                estado_filtrado = (
                    ["PROCESO", "RECHAZADA", "PENDIENTE"]
                    if filter_estado.upper() == "PROCESO"
                    else [filter_estado.upper()]
                )

                registro_medico = RegistroMedico.objects.filter(
                    jugador=jugador,
                    torneo=representante.torneo,
                    estado__in=estado_filtrado
                ).order_by('-fecha_creacion').first()

            if not registro_medico:
                continue  # Saltar jugadores sin ficha médica válida

            jugador_info = {
                "apellido": jugador.persona.profile.apellido,
                "nombre": jugador.persona.profile.nombre,
                "dni": jugador.persona.profile.dni,
                "id": jugador.id,
                "registro_id": registro_medico.id,
                "registro_medico_estado": registro_medico.estado,
                "estudios_medicos": [
                    {
                        'tipo': estudio.get_tipo_estudio_display(),
                        'archivo': estudio.archivo.url if estudio.archivo else None,
                        'observaciones': estudio.observaciones
                    }
                    for estudio in EstudiosMedico.objects.filter(
                        jugador=jugador,
                        fecha_caducidad__gte=date.today()
                    )
                ],
            }

            jugador_info['categorias_equipo'] = [
                {
                    'nombre_categoria': jce.categoria_equipo.categoria.nombre,
                    'nombre_equipo': jce.categoria_equipo.equipo.nombre,
                    'torneo': jce.categoria_equipo.categoria.torneo.nombre
                }
                for jce in jugador.jugadorcategoriaequipo_set.all()
                if jce.categoria_equipo.categoria.torneo == representante.torneo
            ]

            jugadores_info.append(jugador_info)

        context = {
            "representante": representante,
            "jugadores_info": jugadores_info,
            "equipos": equipos,
            "categorias": categorias,
        }
        return render(request, 'representante/torneo_home.html', context)



class TraerEquiposPorCategorias(LoginRequiredMixin, View):
    def get(self, request):
        category_id = request.GET.get('category_id')
        if category_id:
            try:
                categoria = get_object_or_404(Categoria, id=category_id)
                equipos = Equipo.objects.filter(categoria_equipos__categoria=categoria).values('id', 'nombre').distinct()
                return JsonResponse({'equipos': list(equipos)})
            except Categoria.DoesNotExist:
                return JsonResponse({'error': 'Categoría no encontrada.'}, status=404)
        return JsonResponse({'error': 'ID de categoría no proporcionado.'}, status=400)




def obtener_jugadores_por_equipo(equipo_id, torneo_id):
    return Jugador.objects.filter(
        jugadorcategoriaequipo__categoria_equipo__equipo_id=equipo_id,
        jugadorcategoriaequipo__categoria_equipo__categoria__torneo_id=torneo_id
    ).distinct()
def obtener_equipos_por_categoria(categoria_id):
    # Obtener la categoría seleccionada
    categoria = get_object_or_404(Categoria, id=categoria_id)

    # Filtrar las relaciones de CategoriaEquipo asociadas a la categoría
    categorias_equipos = CategoriaEquipo.objects.filter(categoria=categoria)

    # Obtener los equipos únicos asociados a la categoría
    equipos = [ce.equipo for ce in categorias_equipos]
    equipos = list(set(equipos))
    print(equipos)

    return equipos

def obtener_jugadores_por_torneo(torneo_id):
    # Obtener todos los jugadores del torneo
    jugadores_categoria_equipos = JugadorCategoriaEquipo.objects.filter(
        categoria_equipo__categoria__torneo_id=torneo_id
    ).distinct()

    return [jce.jugador for jce in jugadores_categoria_equipos]


def traer_equipos(request):
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria_id')
        if categoria_id:
            categoria = Categoria.objects.get(id=categoria_id)
            equipos = Equipo.objects.filter(categoria_equipos__categoria=categoria).values('id', 'nombre')
            return JsonResponse({'equipos': list(equipos)})
    return JsonResponse({'error': 'Solicitud inválida'}, status=400)


@login_required
def colegio_home_view(request):
    profile_id = request.session.get("user_profile_id")
    representante = get_object_or_404(RepresenteColegio, Profile_id=profile_id)
    colegio = representante.colegio

    buscar = request.GET.get("buscar")
    dni = request.GET.get("dni")
    estado = request.GET.get("estado")
    anio = request.GET.get("anio")
    tipo = request.GET.get("tipo")  # ✅ nuevo parámetro

    estudiantes = Estudiante.objects.none()

    # Si se selecciona tipo alumno sin más filtros, traemos todos
    if tipo == "alumno" and not buscar and not dni and not estado and not anio:
        estudiantes = Estudiante.objects.filter(
            estudiantecolegio__colegio=colegio,
            estudiantecolegio__activo=True
        ).distinct()
    elif tipo == "alumno" or buscar or dni or estado or anio:
        estudiantes = Estudiante.objects.filter(
            estudiantecolegio__colegio=colegio,
            estudiantecolegio__activo=True
        ).distinct()

        if buscar:
            estudiantes = estudiantes.filter(
                Q(nombre__icontains=buscar) |
                Q(apellido__icontains=buscar)
            )

        if dni:
            estudiantes = estudiantes.filter(dni__icontains=dni)

        if estado:
            estudiantes = estudiantes.filter(cus__estado=estado).distinct()

        if anio:
            estudiantes = estudiantes.filter(cus__fecha_de_llenado__year=anio).distinct()

    total_alumnos = None
    total_aprobados = None

    if tipo == "alumno":
        total_alumnos = Estudiante.objects.filter(
            estudiantecolegio__colegio=colegio,
            estudiantecolegio__activo=True
        ).distinct().count()

        total_aprobados = Estudiante.objects.filter(
            estudiantecolegio__colegio=colegio,
            estudiantecolegio__activo=True,
            cus__estado="APROBADA"
        ).distinct().count()

    current_year = datetime.now().year
    anios = list(range(current_year, current_year - 6, -1))

    return render(request, "representante/colegio_home.html", {
        "colegio": colegio,
        "estudiantes": estudiantes,
        "anios": anios,
        "tipo": tipo,  # 🔁 mantener valor en el select del template
        "total_alumnos": total_alumnos,
        "total_aprobados": total_aprobados,
    })


# Vistas para os aptos Generales
class RepresentanteActividadGeneralHomeView(LoginRequiredMixin, View):
    def get(self, request):
        profile_id = request.session.get("user_profile_id")
        profile = get_object_or_404(Profile, id=profile_id)

        representante = RepresentanteActividadGeneral.objects.filter(profile=profile).first()
        if not representante:
            return render(request, 'representante/actividad_general_home.html', {
                "error": "No se encontró información del representante asociado a una actividad general."
            })

        actividad = representante.actividad

        # --- Filtros ---
        search_query = request.GET.get("search_query", "").strip()
        filter_estados = request.GET.getlist("filter_estado")
        fecha_inicio = request.GET.get("fecha_inicio")
        fecha_fin = request.GET.get("fecha_fin")
        accion_rapida = request.GET.get("accion_rapida")

        aptos = AptoGeneral.objects.none()
        filtros_activos = any([search_query, filter_estados, fecha_inicio, fecha_fin, accion_rapida])

        if filtros_activos:
            aptos = AptoGeneral.objects.filter(actividad=actividad)

            # Buscar por nombre, apellido o DNI
            if search_query:
                aptos = aptos.filter(
                    Q(jugador__persona__profile__dni__icontains=search_query) |
                    Q(jugador__persona__profile__nombre__icontains=search_query) |
                    Q(jugador__persona__profile__apellido__icontains=search_query)
                )

            # Filtrar por estados múltiples
            if filter_estados:
                aptos = aptos.filter(estado__in=[e.upper() for e in filter_estados])

            # Rango de fechas
            if fecha_inicio:
                aptos = aptos.filter(fecha_creacion__gte=fecha_inicio)
            if fecha_fin:
                aptos = aptos.filter(fecha_creacion__lte=fecha_fin)

            # Acciones rápidas
            if accion_rapida == "aprobados":
                aptos = aptos.filter(estado="APROBADA")
            elif accion_rapida == "pendientes":
                aptos = aptos.filter(estado__in=["PROCESO", "PENDIENTE"])

        # --- Resumen general ---
        resumen = {
            "aprobados": AptoGeneral.objects.filter(actividad=actividad, estado="APROBADA").count(),
            "rechazados": AptoGeneral.objects.filter(actividad=actividad, estado="RECHAZADO").count(),
            "proceso": AptoGeneral.objects.filter(actividad=actividad, estado__in=["PROCESO", "PENDIENTE"]).count(),
        }

        # --- Construcción de datos para la tabla ---
        jugadores_info = []
        for apto in aptos:
            jugador = apto.jugador
            estudios_count = EstudiosAptoGeneral.objects.filter(apto=apto).count()

            jugadores_info.append({
                "apellido": jugador.persona.profile.apellido,
                "nombre": jugador.persona.profile.nombre,
                "dni": jugador.persona.profile.dni,
                "id": jugador.id,
                "apto_id": apto.id,
                "apto_estado": apto.estado,
                "fecha_creacion": apto.fecha_creacion,
                "fecha_caducidad": apto.fecha_caducidad,
                "estudios_count": estudios_count,  # ✅ nuevo campo
            })

        # --- Contexto para el template ---
        context = {
            "representante": representante,
            "actividad": actividad,
            "jugadores_info": jugadores_info,
            "filter_estados": filter_estados,
            "search_query": search_query,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "resumen": resumen,
        }
        return render(request, "representante/actividad_general_home.html", context)

@login_required
def ver_estudios_representante(request):
    """
    Permite al representante ver los estudios médicos de un jugador
    a través del ID de un Apto General.
    """
    apto_id = request.GET.get("apto_id")

    if not apto_id:
        return render(request, "representante/ver_estudios_jugador.html", {
            "error": "No se especificó el apto.",
            "estudios": [],
        })

    apto = get_object_or_404(AptoGeneral, id=apto_id)
    estudios = (
        EstudiosAptoGeneral.objects
        .filter(apto=apto)
        .select_related("apto")
        .order_by("-fecha_creacion")
    )

    context = {
        "apto": apto,
        "estudios": estudios,
    }

    return render(request, "representante/ver_estudios_jugador.html", context)

@login_required
def estadisticas_colegio(request):
    profile_id = request.session.get("user_profile_id")
    representante = get_object_or_404(RepresenteColegio, Profile_id=profile_id)
    colegio = representante.colegio

    # Estudiantes asociados
    estudiantes = Estudiante.objects.filter(estudiantecolegio__colegio=colegio).distinct()
    total_alumnos = estudiantes.count()

    # CUS asociados
    cus_qs = Cus.objects.filter(estudiante__in=estudiantes)
    total_cus = cus_qs.count()

    # === ESTADOS ===
    total_aprobadas = cus_qs.filter(estado="APROBADA").count()
    total_proceso = cus_qs.filter(estado="PROCESO").count()
    total_rechazadas = cus_qs.filter(estado="RECHAZADA").count()
    total_vencidas = cus_qs.filter(estado="VENCIDO").count()

    # === EXAMEN FÍSICO ===
    fisicos = ExamenFisico.objects.filter(cus__in=cus_qs)
    imc_promedio = fisicos.aggregate(Avg("imc"))["imc__avg"] or 0
    peso_promedio = fisicos.aggregate(Avg("peso"))["peso__avg"] or 0
    talla_promedio = fisicos.aggregate(Avg("talla"))["talla__avg"] or 0

    bajo_peso = fisicos.filter(diagnostico_antropometrico="Bajo peso").count()
    peso_ideal = fisicos.filter(diagnostico_antropometrico="Peso Ideal").count()
    sobrepeso = fisicos.filter(diagnostico_antropometrico="Sobrepeso").count()
    obesidad = fisicos.filter(diagnostico_antropometrico__icontains="Obesidad").count()

    # === EXAMEN CARDIOVASCULAR ===
    cardio_qs = ExamenCardiovascular.objects.filter(cus__in=cus_qs)
    total_cardio = cardio_qs.count()

    sistolicas, diastolicas = [], []
    for examen in cardio_qs:
        if examen.tension_arterial and "/" in examen.tension_arterial:
            try:
                sist, dias = examen.tension_arterial.split("/")
                sistolicas.append(int(sist))
                diastolicas.append(int(dias))
            except ValueError:
                pass

    promedio_sistolica = round(mean(sistolicas), 1) if sistolicas else 0
    promedio_diastolica = round(mean(diastolicas), 1) if diastolicas else 0

    # Clasificación presión arterial
    normales = sum(1 for s in sistolicas if s < 130)
    altas = sum(1 for s in sistolicas if 130 <= s < 140)
    hipertensos = sum(1 for s in sistolicas if s >= 140)

    # Arritmias y soplos
    con_arritmia = cardio_qs.filter(arritmia__icontains="si").count()
    con_soplos = cardio_qs.filter(soplos__icontains="si").count()

    porc_arritmia = round((con_arritmia / total_cardio) * 100, 1) if total_cardio else 0
    porc_soplos = round((con_soplos / total_cardio) * 100, 1) if total_cardio else 0

    # === EXAMEN RESPIRATORIO ===
    resp_qs = ExamenRespiratorio.objects.filter(cus__in=cus_qs)
    total_resp = resp_qs.count()
    resp_anormales = resp_qs.exclude(detalles__isnull=True).exclude(detalles="").count()
    porc_resp_anormales = round((resp_anormales / total_resp) * 100, 1) if total_resp else 0

    # === RESTO DE EXÁMENES ===
    odontologicos = ExamenOdontologico.objects.filter(cus__in=cus_qs).exclude(detalles__isnull=True).exclude(detalles="").count()

    oftalmologicos = ExamenOftalmologico.objects.filter(
        cus__in=cus_qs
    ).filter(Q(usa_anteojos=True) | Q(otros__isnull=False, otros__gt="")).count()

    fonoaudiologicos = ExamenFonoaudiologico.objects.filter(
        cus__in=cus_qs
    ).exclude(detalles__isnull=True).exclude(detalles="").count()

    osteoarticulares = ExamenOsteoarticular.objects.filter(
        cus__in=cus_qs
    ).filter(Q(cifosis=True) | Q(lordosis=True) | Q(escoliosis=True)).count()

    neurologicos = ExamenNeurologico.objects.filter(
        cus__in=cus_qs
    ).exclude(detalles__isnull=True).exclude(detalles="").count()

    # === EXAMEN OSTEOARTICULAR DETALLADO ===
    osteo_qs = ExamenOsteoarticular.objects.filter(cus__in=cus_qs)
    total_osteo = osteo_qs.count()

    columna_normal = osteo_qs.filter(columna_normal=True).count()
    cifosis = osteo_qs.filter(cifosis=True).count()
    lordosis = osteo_qs.filter(lordosis=True).count()
    escoliosis = osteo_qs.filter(escoliosis=True).count()

    alteraciones = cifosis + lordosis + escoliosis
    porc_alteraciones = round((alteraciones / total_osteo) * 100, 1) if total_osteo else 0
    porc_columna_normal = round((columna_normal / total_osteo) * 100, 1) if total_osteo else 0

    # === CONTEXTO ===
    context = {
        "colegio": colegio,
        "total_alumnos": total_alumnos,
        "total_cus": total_cus,
        "total_aprobadas": total_aprobadas,
        "total_proceso": total_proceso,
        "total_rechazadas": total_rechazadas,
        "total_vencidas": total_vencidas,

        "imc_promedio": round(imc_promedio, 2),
        "peso_promedio": round(peso_promedio, 2),
        "talla_promedio": round(talla_promedio, 2),
        "bajo_peso": bajo_peso,
        "peso_ideal": peso_ideal,
        "sobrepeso": sobrepeso,
        "obesidad": obesidad,

        # Cardiovascular
        "promedio_sistolica": promedio_sistolica,
        "promedio_diastolica": promedio_diastolica,
        "normales": normales,
        "altas": altas,
        "hipertensos": hipertensos,
        "porc_arritmia": porc_arritmia,
        "porc_soplos": porc_soplos,
        "total_cardio": total_cardio,

        # Respiratorio
        "total_resp": total_resp,
        "resp_anormales": resp_anormales,
        "porc_resp_anormales": porc_resp_anormales,

        # Otros
        "odontologicos": odontologicos,
        "oftalmologicos": oftalmologicos,
        "fonoaudiologicos": fonoaudiologicos,
        "osteoarticulares": osteoarticulares,
        "neurologicos": neurologicos,

        # Osteoarticular

        "total_osteo": total_osteo,
        "columna_normal": columna_normal,
        "cifosis": cifosis,
        "lordosis": lordosis,
        "escoliosis": escoliosis,
        "porc_alteraciones": porc_alteraciones,
        "porc_columna_normal": porc_columna_normal,
    }

    return render(request, "estadisticas/estadisticas_home.html", context)