from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import datetime
import random
import string
from pymongo import MongoClient

# Conexión real a tu Cluster de MongoDB Atlas
MONGO_URI = "mongodb+srv://admin:admin@cluster0.1zebucq.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['mahanaym_db']

# Colecciones NoSQL unificadas
coleccion_clases = db['clases_videos']
coleccion_tareas = db['entregas_tareas']
coleccion_examenes = db['examenes_moodle']
coleccion_respuestas_examenes = db['respuestas_examenes']

# --- VISTAS DEL FRONTEND (HTML) ---
class VistaLogin(TemplateView):
    template_name = "plataforma/login.html"

    def post(self, request, *args, **kwargs):
        user_raw = request.POST.get('username')
        pass_raw = request.POST.get('password')
        usuario = authenticate(request, username=user_raw, password=pass_raw)
        
        if usuario is not None:
            login(request, usuario)
            response = redirect('vista_dashboard')
            refresh = RefreshToken.for_user(usuario)
            response.set_cookie('jwt_access_token', str(refresh.access_token))
            response.set_cookie('nombre_usuario', usuario.username)
            return response
        else:
            return self.render_to_response({"error": "Credenciales inválidas."})

class VistaDashboard(LoginRequiredMixin, TemplateView):
    template_name = "plataforma/dashboard.html"
    login_url = '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        es_profesor = self.request.user.groups.filter(name='Profesores').exists()
        context['rol'] = 'Profesor' if es_profesor else 'Estudiante'
        return context

class VistaLogout(APIView):
    def get(self, request):
        logout(request)
        response = redirect('vista_login')
        response.delete_cookie('jwt_access_token')
        response.delete_cookie('nombre_usuario')
        return response


# --- ENDPOINTS API (BACKEND) ---

class ListarEstudiantesView(APIView):
    """ Retorna todos los estudiantes registrados en el sistema (Moodle Directory) """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filtramos los usuarios que no pertenecen al grupo de profesores ni son superadmins
        estudiantes = User.objects.filter(is_superuser=False, groups__name__isnull=True).values('id', 'username', 'email')
        return Response({"status": "Exitoso", "estudiantes": list(estudiantes)}, status=status.HTTP_200_OK)


class ListarClasesEstudianteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        username = request.user.username
        clases = list(coleccion_clases.find({"alumnos_permitidos": username}))
        for c in clases:
            c.pop('_id', None)
        return Response({"status": "Exitoso", "clases": clases}, status=status.HTTP_200_OK)


class SubirVideoClaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.groups.filter(name='Profesores').exists():
            return Response({"error": "No eres un profesor."}, status=status.HTTP_403_FORBIDDEN)

        titulo = request.data.get('titulo')
        materia = request.data.get('materia')
        video_file = request.FILES.get('video')
        estudiantes_raw = request.data.get('estudiantes_assigned', '')

        if not titulo or not materia or not video_file:
            return Response({"error": "Faltan campos obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        lista_alumnos = [algo.strip() for algo in estudiantes_raw.split(',') if algo.strip()]
        codigo_clase = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        documento_clase = {
            "codigo_clase": codigo_clase,
            "profesor": request.user.username,
            "titulo": titulo,
            "materia": materia,
            "nombre_archivo": video_file.name,
            "url_reproductor": f"/static/uploads/{video_file.name}", # Simula descarga de archivo local
            "alumnos_permitidos": lista_alumnos,
            "estudiantes_completados": [],
            "fecha_creacion": str(datetime.date.today())
        }
        
        coleccion_clases.insert_one(documento_clase)
        documento_clase.pop('_id', None)
        return Response({"status": "Exitoso", "codigo_clase": codigo_clase, "datos": documento_clase}, status=status.HTTP_201_CREATED)


class SubirTareaEstudianteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        codigo_clase = request.data.get('codigo_clase')
        archivo_tarea = request.FILES.get('tarea')

        if not codigo_clase or not archivo_tarea:
            return Response({"error": "Faltan campos obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        clase = coleccion_clases.find_one({"codigo_clase": codigo_clase.upper()})
        if not clase:
            return Response({"error": "Código de clase no válido."}, status=status.HTTP_404_NOT_FOUND)

        total_tareas = coleccion_tareas.count_documents({})
        documento_tarea = {
            "entrega_id": f"ent_{total_tareas + 500}",
            "codigo_clase": codigo_clase.upper(),
            "materia": clase['materia'],
            "estudiante": request.user.username,
            "archivo_adjunto": archivo_tarea.name,
            "nota": "Sin calificar",
            "ponderacion_maxima": 10.0, # Moodle Base Ponderación
            "nota_ponderada": 0.0,
            "comentario_profesor": "",
            "fecha_entrega": str(datetime.datetime.now())
        }
        
        coleccion_tareas.insert_one(documento_tarea)
        documento_tarea.pop('_id', None)
        return Response({"status": "Exitoso", "datos": documento_tarea}, status=status.HTTP_201_CREATED)


class ListarTareasPendientesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tareas = list(coleccion_tareas.find({}))
        for t in tareas:
            t.pop('_id', None)
        return Response({"status": "Exitoso", "tareas": tareas}, status=status.HTTP_200_OK)


class CalificarTareaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        entrega_id = request.data.get('entrega_id')
        nota_obtenida = float(request.data.get('nota', 0))
        ponderacion = float(request.data.get('ponderacion', 10)) # Entrada de ponderación del profesor

        # Moodle Formula: (Nota Obtenida / Base 10) * Ponderación Elegida
        nota_ponderada = (nota_obtenida / 10.0) * ponderacion

        resultado = coleccion_tareas.update_one(
            {"entrega_id": entrega_id},
            {"$set": {
                "nota": nota_obtenida,
                "ponderacion_maxima": ponderacion,
                "nota_ponderada": round(nota_ponderada, 2),
                "comentario_profesor": "Evaluado con ponderación Moodle"
            }}
        )
        return Response({"status": "Exitoso", "mensaje": "Calificación calculada con éxito."}, status=status.HTTP_200_OK)


class VerNotasEstudianteView(APIView):
    """ Permite al estudiante ver su libreta de calificaciones en tiempo real """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        username = request.user.username
        mis_tareas = list(coleccion_tareas.find({"estudiante": username}))
        mis_examenes = list(coleccion_respuestas_examenes.find({"estudiante": username}))
        
        for t in mis_tareas: t.pop('_id', None)
        for e in mis_examenes: e.pop('_id', None)
            
        return Response({
            "status": "Exitoso",
            "tareas_calificadas": mis_tareas,
            "examenes_realizados": mis_examenes
        }, status=status.HTTP_200_OK)


# --- EXÁMENES INTERACTIVOS INTERFAZ (MOODLE QUIZ) ---

class CrearExamenView(APIView):
    """ Profesor crea una prueba con pregunta y respuesta correcta """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        codigo_clase = request.data.get('codigo_clase')
        pregunta = request.data.get('pregunta')
        opcion_a = request.data.get('opcion_a')
        opcion_b = request.data.get('opcion_b')
        correcta = request.data.get('correcta') # 'A' o 'B'

        doc_examen = {
            "examen_id": f"quiz_{''.join(random.choices(string.digits, k=4))}",
            "codigo_clase": codigo_clase.upper(),
            "pregunta": pregunta,
            "opciones": {"A": opcion_a, "B": opcion_b},
            "correcta": correcta.upper()
        }
        coleccion_examenes.insert_one(doc_examen)
        doc_examen.pop('_id', None)
        return Response({"status": "Exitoso", "examen": doc_examen}, status=status.HTTP_201_CREATED)


class ObtenerExamenClaseView(APIView):
    """ Estudiante descarga la prueba activa de su asignatura """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        codigo = request.query_params.get('codigo_clase')
        examen = coleccion_examenes.find_one({"codigo_clase": codigo.upper()})
        if not examen:
            return Response({"error": "No hay pruebas activas para esta clase."}, status=status.HTTP_404_NOT_FOUND)
        examen.pop('_id', None)
        return Response({"status": "Exitoso", "examen": examen}, status=status.HTTP_200_OK)


class ResponderExamenView(APIView):
    """ Estudiante envía su respuesta y el sistema la califica automáticamente """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        examen_id = request.data.get('examen_id')
        respuesta_alumno = request.data.get('respuesta') # 'A' o 'B'
        username = request.user.username

        examen = coleccion_examenes.find_one({"examen_id": examen_id})
        if not examen:
            return Response({"error": "Examen no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        es_correcta = (respuesta_alumno.upper() == examen['correcta'])
        nota_final = 10.0 if es_correcta else 0.0

        doc_respuesta = {
            "examen_id": examen_id,
            "estudiante": username,
            "materia": "Evaluación Virtual",
            "respuesta_enviada": respuesta_alumno.upper(),
            "resultado": "Aprobado" if es_correcta else "Reprobado",
            "nota": nota_final
        }
        coleccion_respuestas_examenes.insert_one(doc_respuesta)
        doc_respuesta.pop('_id', None)
        return Response({"status": "Exitoso", "evaluacion": doc_respuesta}, status=status.HTTP_200_OK)


class MarcarClaseCompletadaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        codigo = request.data.get('codigo_clase')
        username = request.user.username
        coleccion_clases.update_one({"codigo_clase": codigo.upper()}, {"$addToSet": {"estudiantes_completados": username}})
        return Response({"status": "Exitoso"})