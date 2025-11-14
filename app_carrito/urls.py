from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import CarritoViewSet
from .item_api import ItemCarritoViewSet

router = DefaultRouter()
router.register(r'carritos', CarritoViewSet, basename='carrito')
router.register(r'items', ItemCarritoViewSet, basename='item-carrito')

urlpatterns = [
    path('', include(router.urls)),
]