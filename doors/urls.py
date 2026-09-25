from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),

    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("my-doors/", views.my_doors, name="my_doors"),
    path("add/", views.add_door, name="add_door"),
    path("edit/<int:pk>/", views.edit_door, name="edit_door"),
    path("delete/<int:pk>/", views.delete_door, name="delete_door"),

    path("like/<int:door_id>/", views.toggle_like, name="toggle_like"),
    path("comment/<int:door_id>/", views.add_comment, name="add_comment"),
    path("send-telegram-order/<int:door_id>/", views.send_telegram_order, name="send_order"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)