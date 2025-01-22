from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name="inicio"),
    path('nosotros/', views.nosotros, name="nosotros"),
    path('contacto/', views.contacto, name='contacto'),
    path('productos/', views.productos, name='productos'),
    path('producto/<int:producto_id>/', views.producto_detail, name='producto_detail'),
    path('api/obtener_tipos/', views.obtener_tipos, name='obtener_tipos'),  # Nueva ruta para AJAX
    path('carrito/', views.ver_carrito, name='ver_carrito'),
]
