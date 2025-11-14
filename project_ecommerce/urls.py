
from django.contrib import admin
from django.urls import path , include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('app_user.urls')),
    path('api/clientes/', include('app_Cliente.urls')),
    path('api/carrito/', include('app_carrito.urls')),
    path('api/compras/', include('app_compras.urls')),
    path('api/pedidos/', include('app_pedidos.urls')),
    path('api/productos/', include('app_productos.urls')),
]
