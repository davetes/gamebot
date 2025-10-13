"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from api.views import (
    leaderboard_view,
    list_pending_deposits,
    approve_deposit,
    list_admin_txns,
    add_admin_txn,
    bulk_add_admin_txns,
    upload_receipt,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/leaderboard', leaderboard_view, name='api_leaderboard'),
    path('api/admin/deposits', list_pending_deposits, name='api_admin_deposits'),
    path('api/admin/deposits/<int:deposit_id>/approve', approve_deposit, name='api_admin_approve_deposit'),
    path('api/admin/txns', list_admin_txns, name='api_admin_txns'),
    path('api/admin/txns/add', add_admin_txn, name='api_admin_txns_add'),
    path('api/admin/txns/bulk', bulk_add_admin_txns, name='api_admin_txns_bulk'),
    path('api/upload-receipt', upload_receipt, name='api_upload_receipt'),
]
