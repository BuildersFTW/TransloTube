from django.urls import path
from . import views


urlpatterns = [
    path('', views.home_page),
    path('watch', views.watch),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('quiz/', views.quiz, name='quiz')

]