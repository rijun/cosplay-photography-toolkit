from django.urls import path

from . import views

app_name = 'gallery'

urlpatterns = [
    path('g/<str:token>', views.view_gallery, name='view_gallery'),
    path('g/<str:token>/photos/<int:photo_id>/select', views.toggle_selection, name='toggle_selection'),
    path('g/<str:token>/photos/<int:photo_id>/comment', views.add_comment, name='add_comment'),
    path('g/<str:token>/photos/<int:photo_id>/comments', views.get_comments, name='get_comments'),
]
