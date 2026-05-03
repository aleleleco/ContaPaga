from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('conta/nova/', views.conta_create, name='conta_create'),
    path('conta/<int:pk>/editar/', views.conta_edit, name='conta_edit'),
    path('conta/<int:pk>/deletar/', views.conta_delete, name='conta_delete'),
    path('lancamento/novo/', views.lancamento_create, name='lancamento_create'),
    path('pagamento/<int:pk>/registrar/', views.pagamento_registrar, name='pagamento_registrar'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('parcelamentos/', views.parcelamentos_list, name='parcelamentos_list'),
    path('parcelamentos/<int:pk>/editar/', views.parcelamento_edit, name='parcelamento_edit'),
    path('parcelamentos/<int:pk>/deletar/', views.parcelamento_delete, name='parcelamento_delete'),
    path('parcelamentos/<int:pk>/detalhe/', views.parcelamento_detalhe, name='parcelamento_detalhe'),
    path('competencias/', views.competencias_list, name='competencias_list'),
    path('competencias/<int:pk>/reabrir/', views.competencia_reabrir, name='competencia_reabrir'),
    path('competencias/<int:pk>/exportar/', views.exportar_pdf, name='exportar_pdf'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),
    path('categoria/nova/', views.categoria_create, name='categoria_create'),
    path('categoria/<int:pk>/deletar/', views.categoria_delete, name='categoria_delete'),
    path('agente/novo/', views.agente_create, name='agente_create'),
    path('agente/<int:pk>/editar/', views.agente_edit, name='agente_edit'),
    path('agente/<int:pk>/deletar/', views.agente_delete, name='agente_delete'),
    path('legacy/', views.legacy_hub, name='legacy_hub'),
    path('legacy/migrate/conta/<int:legacy_id>/', views.legacy_migrate_conta, name='legacy_migrate_conta'),
    path('legacy/migrate/lancamento/<int:legacy_id>/', views.legacy_migrate_lancamento, name='legacy_migrate_lancamento'),
    path('legacy/migrate/competencia/<int:legacy_comp_id>/', views.legacy_migrate_competencia, name='legacy_migrate_competencia'),
    path('legacy/migrate/parcelamento/<int:legacy_id>/', views.legacy_migrate_parcelamento, name='legacy_migrate_parcelamento'),
]
