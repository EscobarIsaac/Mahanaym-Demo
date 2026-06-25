from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView
from plataforma.views import (
    SubirVideoClaseView, SubirTareaEstudianteView, ListarClasesEstudianteView,
    ListarTareasPendientesView, CalificarTareaView, MarcarClaseCompletadaView,
    ListarEstudiantesView, VerNotasEstudianteView, CrearExamenView, 
    ObtenerExamenClaseView, ResponderExamenView, VistaLogin, VistaDashboard, VistaLogout
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Renderizados Web Frontend
    path('', VistaLogin.as_view(), name='vista_login'),
    path('dashboard/', VistaDashboard.as_view(), name='vista_dashboard'),
    path('logout/', VistaLogout.as_view(), name='vista_logout'),
    
    # Endpoints de Servicios Backend API
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/estudiante/estudiantes-activos/', ListarEstudiantesView.as_view(), name='estudiantes_activos'),
    path('api/profesor/subir-video/', SubirVideoClaseView.as_view(), name='subir_video'),
    path('api/profesor/listar-tareas/', ListarTareasPendientesView.as_view(), name='listar_tareas'),
    path('api/profesor/calificar/', CalificarTareaView.as_view(), name='calificar_tarea'),
    path('api/profesor/crear-examen/', CrearExamenView.as_view(), name='crear_examen'),
    
    path('api/estudiante/mis-clases/', ListarClasesEstudianteView.as_view(), name='mis_clases'),
    path('api/estudiante/subir-tarea/', SubirTareaEstudianteView.as_view(), name='subir_tarea'),
    path('api/estudiante/ver-notas/', VerNotasEstudianteView.as_view(), name='ver_notes'),
    path('api/profesor/obtener-examen/', ObtenerExamenClaseView.as_view(), name='obtener_examen'),
    path('api/profesor/responder-examen/', ResponderExamenView.as_view(), name='responder_examen'),
]