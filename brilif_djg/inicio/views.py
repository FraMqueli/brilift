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


from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
import uuid
from .models import Producto
from .views import PROCESO_MAPPING  # Asegúrate de importar tu mapeo correctamente

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

    # Recopilar imágenes disponibles (asumiendo que tienes imagen_1 a imagen_4)
    imagenes = []
    for i in range(1, 5):
        imagen_attr = f'imagen_{i}'
        imagen = getattr(producto, imagen_attr, None)
        if imagen:
            imagenes.append(imagen.url)

    # Manejo de cookies para los "likes"
    user_cookie = request.COOKIES.get('user_cookie', None)
    if not user_cookie:
        user_cookie = str(uuid.uuid4())

    # Obtener los productos a los que el usuario ya le ha dado "Me Gusta"
    liked_products = request.COOKIES.get(f'liked_products_{user_cookie}', '')
    liked_products = liked_products.split(',') if liked_products else []
    producto_liked = str(producto.id) in liked_products

    # Manejar la solicitud POST para incrementar "Me Gusta"
    if request.method == 'POST':
        # Si ya dio "Me Gusta", no permitimos otro
        if producto_liked:
            return JsonResponse({
                'success': False,
                'error': 'Ya diste Me Gusta a este producto'
            }, status=400)
        
        # Incrementar el contador y guardar el like
        producto.cantidad_me_gusta += 1
        producto.save()

        liked_products.append(str(producto.id))
        response = JsonResponse({
            'success': True,
            'likes_count': producto.cantidad_me_gusta
        })

        # Setear las cookies con el identificador del usuario y los productos "liked"
        response.set_cookie('user_cookie', user_cookie, max_age=60*60*24*365)
        response.set_cookie(f'liked_products_{user_cookie}', ','.join(liked_products), max_age=60*60*24*365)

        return response

    # Para solicitudes GET: renderizar la plantilla con la información del producto,
    # incluyendo si ya se le dio "Me Gusta" o no.
    response = render(request, 'inicio/producto_detail.html', {
        'producto': producto,
        'combustible': combustible,
        'imagenes': imagenes,
        'producto_liked': producto_liked,
    })
    response.set_cookie('user_cookie', user_cookie, max_age=60*60*24*365)
    return response




def get_proceso_info(proceso):
    """Obtiene la información de mapeo para un proceso específico"""
    return PROCESO_MAPPING.get(proceso, {})

def obtener_tipos(request):
    """Vista para obtener tipos de proceso vía AJAX"""
    proceso = request.GET.get('procesos')
    
    # Añadir prints para debugging
    print(f"Proceso recibido: {proceso}")
    
    if proceso:
        proceso = proceso.replace(' ', '_').upper()  # Asegurarnos que está en mayúsculas
    
    proceso_info = get_proceso_info(proceso)
    print(f"Proceso info encontrada: {proceso_info}")

    if not proceso_info:
        return JsonResponse({'tipos': [], 'error': 'Proceso no encontrado'})
    
    tipos = proceso_info['tipo_modelo'].objects.filter(activo=True)
    print(f"Tipos encontrados: {tipos.count()}")
    
    tipos_data = [{'id': tipo.id, 'nombre': tipo.nombre} for tipo in tipos]
    
    return JsonResponse({
        'tipos': tipos_data,
    })

def productos(request):
    """
    Vista principal de productos con filtros dinámicos y búsqueda.
    """
    # Obtener todos los productos
    productos = Producto.objects.all()

    # Filtros existentes
    search_query = request.GET.get('search', '').strip()
    proceso = request.GET.get('procesos', '')
    categoria_filter = request.GET.get('categoria', '')
    estado_filter = request.GET.get('estado', '')
    combustible_filter = request.GET.get('combustible', '')
    
    # Nuevo: Filtro por tipo (dinámico)
    tipo_filter = request.GET.get('tipo')
    
    # Aplicar búsqueda
    if search_query:
        productos = productos.filter(
            Q(nombre__icontains=search_query) | Q(descripcion__icontains=search_query)
        )

    # Aplicar filtro por proceso
    if proceso:
        productos = productos.filter(procesos=proceso)
        
        # Aplicar filtro dinámico por tipo si existe
        if tipo_filter:
            proceso_info = PROCESO_MAPPING.get(proceso, {})
            if proceso_info:
                modelo = proceso_info['modelo']
                # Construir el filtro dinámicamente
                tipo_filter_key = f"{modelo}__tipo"
                productos = productos.filter(**{tipo_filter_key: tipo_filter})

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

    # Obtener el tipo actual para el contexto
    tipo_actual = None
    if proceso and tipo_filter:
        proceso_info = PROCESO_MAPPING.get(proceso)
        if proceso_info:
            try:
                tipo_actual = proceso_info['tipo_modelo'].objects.get(id=tipo_filter)
            except proceso_info['tipo_modelo'].DoesNotExist:
                pass

    # Asignar combustible_display a cada producto
    for producto in productos:
        producto.combustible_display = None
        for modelo in ['gruahorquilla', 'alzahombre', 'brazoarticulado', 'plataformadeelevacion']:
            if hasattr(producto, modelo):
                equipo = getattr(producto, modelo)
                if equipo and hasattr(equipo, 'combustible'):
                    producto.combustible_display = equipo.combustible
                    break

    # Obtener procesos disponibles
    procesos = dict(Producto.PROCESOS_CHOICES)

    # Determinar el proceso actual y su versión limpia
    proceso_actual = proceso
    proceso_limpio = procesos.get(proceso_actual, '').replace('_', ' ').title() if proceso_actual else None

    context = {
        'productos': productos,
        'combustibles': Combustible.choices,
        'procesos': procesos,
        'proceso_actual': proceso_actual,
        'proceso_limpio': proceso_limpio,
        'categoria_actual': categoria_filter,
        'estado_actual': estado_filter,
        'combustible_actual': combustible_filter,
        'tipo_actual': tipo_actual,  # Añadido para mantener el estado del filtro
        'estados': Producto.ESTADO_CHOICES,
        'categorias': Producto.CATEGORIA_CHOICES,
        # Añadir cualquier otro contexto necesario para los filtros dinámicos
    }

    return render(request, 'inicio/productos.html', context)




def ver_carrito(request):
    return render(request, 'carrito/ver_carrito.html')