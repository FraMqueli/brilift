from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Producto

# Sitemap para páginas estáticas
class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        """
        Retorna una lista con los 'name' de las rutas estáticas 
        definidas en tu urls.py.
        """
        return [
            'inicio', 
            'nosotros', 
            'contacto', 
            'productos', 
            'ver_carrito'
        ]

    def location(self, item):
        return reverse(item)

# Sitemap para productos
class ProductoSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    # Opcionalmente, puedes usar lastmod para indicar la fecha de modificación
    # def lastmod(self, obj):
    #     return obj.fecha_actualizacion

    def items(self):
        """
        Retorna los objetos Producto que quieres incluir en el sitemap.
        Por ejemplo, solo los que estén disponibles o todos.
        """
        return Producto.objects.filter(estado='Disponible')

    # Si definiste get_absolute_url en el modelo, Django lo usará automáticamente.
    # En caso de que NO uses get_absolute_url, usa esta función:
    #
    # def location(self, obj):
    #     return reverse('producto_detail', args=[obj.id])
