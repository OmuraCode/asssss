from rest_framework import serializers

from chat.models import Threads


class ChatbotInputSerializer(serializers.Serializer):
    user_input = serializers.CharField()
    user_id = serializers.CharField()

    class Meta:
        model = Threads
        fields = 'user_id'


class ChatbotResponseSerializer(serializers.Serializer):
    response = serializers.CharField()