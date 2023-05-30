from django.urls import path,include

urlpatterns = [
    path('myapp/', include("myapp.urls")),
    # 他のURLパターンを追加することもできます
]
