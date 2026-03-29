from django.urls import path

from . import views

app_name = 'gallery'

urlpatterns = [
    path('g/<str:token>', views.view_gallery, name='view_gallery'),
    path('g/<str:token>/photos/<int:photo_id>/download', views.download_photo, name='download_photo'),
    path('g/<str:token>/photos/<int:photo_id>/flag', views.toggle_flag, name='toggle_flag'),
    path('g/<str:token>/photos/<int:photo_id>/comment', views.add_comment, name='add_comment'),
    path('g/<str:token>/photos/<int:photo_id>/comments', views.get_comments, name='get_comments'),
    path('g/<str:token>/download/start', views.start_zip_download, name='start_zip_download'),
    path('g/<str:token>/download/<uuid:download_id>/progress', views.zip_download_progress, name='zip_download_progress'),
    path('g/<str:token>/download/<uuid:download_id>/file', views.serve_zip_download, name='serve_zip_download'),
]