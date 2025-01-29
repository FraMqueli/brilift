from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail # Enviar un correo con los datos
from django.db.models import Q 
import uuid
from .models import (
    Producto, Combustible, TipoPlataformaDeElevacion, TipoBrazoArticulado, TipoAlzaHombre, TipoGruaHorquilla
)

PROCESO_MAPPING = {
    'ALZA_HOMBRE': {'modelo': 'alzahombre', 'tipo_modelo': TipoAlzaHombre},
    'BRAZO_ARTICULADO': {'modelo': 'brazoarticulado', 'tipo_modelo': TipoBrazoArticulado},
    'GRUA_HORQUILLA': {'modelo': 'gruahorquilla', 'tipo_modelo': TipoGruaHorquilla},
    'PLATAFORMA_DE_ELEVACION': {'modelo': 'plataformadeelevacion', 'tipo_modelo': TipoPlataformaDeElevacion},
}




# views.py

def inicio(request):
    """
    Vista principal para mostrar los productos destacados en la página de inicio.
    """
    # Obtener los productos con más "Me Gusta"
    productos = Producto.objects.all().order_by('-cantidad_me_gusta')[:3]

    # Añadir información adicional a cada producto
    for producto in productos:
        producto.combustible_display = None
        for proceso_key, proceso_info in PROCESO_MAPPING.items():
            modelo = proceso_info['modelo']
            if hasattr(producto, modelo):  # Verificar si existe el atributo relacionado
                equipo = getattr(producto, modelo)
                if equipo and hasattr(equipo, 'combustible'):  # Verificar si el equipo tiene un combustible asociado
                    producto.combustible_display = equipo.combustible
                    break

    # Contexto para la plantilla
    context = {
        'productos': productos,
        'combustibles': Combustible.choices,
    }

    return render(request, 'inicio/inicio.html', context)


    

def nosotros(request):
    return render(request, 'inicio/nosotros.html')

def contacto(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Procesar los datos (enviar correo, guardar en base de datos, etc.)
        # Ejemplo de enviar un correo:
        send_mail(
            'Nuevo mensaje de contacto',
            f'Nombre: {name}\nCorreo: {email}\nMensaje: {message}',
            'framqueli@gmail.com',  # Cambiar por tu correo
            ['framqueli@gmail.com'],  # Cambiar por el correo destinatario
            fail_silently=False,
        )

        return HttpResponse("Gracias por tu mensaje, nos pondremos en contacto pronto.")
    return render(request, 'inicio/contacto.html')


# views.py

def producto_detail(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Obtener el combustible desde el equipo relacionado
    combustible = None
    proceso_info = PROCESO_MAPPING.get(producto.procesos)
    if proceso_info:
        modelo = proceso_info['modelo']
        if hasattr(producto, modelo):
            equipo_relacionado = getattr(producto, modelo)
            if equipo_relacionado and hasattr(equipo_relacionado, 'combustible'):
                combustible = equipo_relacionado.combustible

    context = {
        'producto': producto,
        'combustible': combustible,
    }

    return render(request, 'inicio/producto_detail.html', context)


def get_proceso_info(proceso):
    """Obtiene la información de mapeo para un proceso específico"""
    return PROCESO_MAPPING.get(proceso, {})

def obtener_tipos(request):
    """Vista para obtener tipos de proceso vía AJAX"""
    proceso = request.GET.get('procesos')
    if proceso:
        proceso = proceso.replace(' ', '_')    
    proceso_info = get_proceso_info(proceso)

    if not proceso_info:
        return JsonResponse({'tipos': []})
    
    tipos = proceso_info['tipo_modelo'].objects.filter(activo=True)
    tipos_data = [{'id': tipo.id, 'nombre': tipo.nombre} for tipo in tipos]
    
    # Obtener campos adicionales si existen
    campos_adicionales = {}
    if proceso_info.get('campos_adicionales'):
        modelo_relacionado = proceso_info['modelo']
        for campo in proceso_info['campos_adicionales']:
            valores = Producto.objects.filter(procesos=proceso)\
                .values_list(f'{modelo_relacionado}__{campo}', flat=True)\
                .distinct()
            campos_adicionales[campo] = list(valores)
    
    return JsonResponse({
        'tipos': tipos_data,
        'campos_adicionales': campos_adicionales
    })

def productos(request):
    """
    Vista principal de productos con filtros dinámicos y búsqueda.
    """
    # Obtener todos los productos
    productos = Producto.objects.all()

    # Filtros dinámicos
    search_query = request.GET.get('search', '').strip()
    proceso = request.GET.get('procesos', '')  # Obtiene el proceso seleccionado
    categoria_filter = request.GET.get('categoria', '')
    estado_filter = request.GET.get('estado', '')
    combustible_filter = request.GET.get('combustible', '')

    # Aplicar búsqueda
    if search_query:
        productos = productos.filter(
            Q(nombre__icontains=search_query) | Q(descripcion__icontains=search_query)
        )

    # Aplicar filtro por proceso
    if proceso:
        productos = productos.filter(procesos=proceso)

    # Aplicar filtro por categoría
    if categoria_filter:
        productos = productos.filter(categoria=categoria_filter)

    # Aplicar filtro por estado
    if estado_filter:
        productos = productos.filter(estado=estado_filter)

    # Aplicar filtro por combustible
    if combustible_filter:
        productos = productos.filter(
            Q(gruahorquilla__combustible=combustible_filter) |
            Q(alzahombre__combustible=combustible_filter) |
            Q(brazoarticulado__combustible=combustible_filter) |
            Q(plataformadeelevacion__combustible=combustible_filter)
        )

    # Asignar combustible_display a cada producto
    for producto in productos:
        producto.combustible_display = None  # Inicializa como None
        # Busca en cada modelo relacionado si existe un combustible
        for modelo in ['gruahorquilla', 'alzahombre', 'brazoarticulado', 'plataformadeelevacion']:
            if hasattr(producto, modelo):
                equipo = getattr(producto, modelo)
                if equipo and hasattr(equipo, 'combustible'):
                    producto.combustible_display = equipo.combustible
                    break  # Detiene la búsqueda si encuentra el combustible

    # Obtener procesos disponibles
    procesos = dict(Producto.PROCESOS_CHOICES)

    # Determinar el proceso actual y su versión limpia para el template
    proceso_actual = proceso  # Ejemplo: 'GRUA_HORQUILLA'
    proceso_limpio = procesos.get(proceso_actual, '').replace('_', ' ').title() if proceso_actual else None

    # **AQUÍ SE AÑADEN LOS ESTADOS Y CATEGORÍAS AL CONTEXTO**
    context = {
        'productos': productos,
        'combustibles': Combustible.choices,
        'procesos': procesos,
        'proceso_actual': proceso_actual,
        'proceso_limpio': proceso_limpio,
        'categoria_actual': categoria_filter,
        'estado_actual': estado_filter,
        'combustible_actual': combustible_filter,
        'estados': Producto.ESTADO_CHOICES,  # Agregamos los estados al contexto
        'categorias': Producto.CATEGORIA_CHOICES,  # Agregamos las categorías al contexto
    }

    return render(request, 'inicio/productos.html', context)




def ver_carrito(request):
    return render(request, 'carrito/ver_carrito.html')