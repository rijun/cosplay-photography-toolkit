from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('galleries', views.galleries_view, name='galleries'),
    path('galleries/<slug:slug>/photos', views.register_photo, name='register_photo'),
    path('galleries/<slug:slug>/selections', views.get_selections, name='get_selections'),
    path('galleries/<slug:slug>/archive', views.archive_gallery, name='archive_gallery'),
]
