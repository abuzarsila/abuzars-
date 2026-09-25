from django.conf import settings
from django.contrib import admin
from django.urls import path
from doors import views 
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add/', views.add_door, name='add_door'),
    path('my-doors/', views.my_doors, name='my_doors'),
    path('edit/<int:pk>/', views.edit_door, name='edit_door'),
    path('delete/<int:pk>/', views.delete_door, name='delete_door'),
    path('order/<int:door_id>/', views.send_telegram_order, name='send_order'),
    path('send-telegram-order/<int:door_id>/', views.send_telegram_order, name='send_order_legacy'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    
