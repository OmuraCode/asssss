from django.urls import path
from .views import ChatbotView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('chatbot/', ChatbotView.as_view(), name='chatbot'),
    ]