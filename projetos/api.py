"""API REST (Django REST Framework)."""

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from contas.models import Competencia, Perfil

from . import services
from .models import Interesse, Projeto
from .views import filtrar_projetos


# ---------- Serializers ----------

class CompetenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competencia
        fields = ["id", "nome", "slug"]


class AutorSerializer(serializers.ModelSerializer):
    nome = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["username", "nome"]

    def get_nome(self, obj):
        return obj.get_full_name() or obj.username


class PerfilSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="usuario.username", read_only=True)
    nome = serializers.CharField(source="nome_exibicao", read_only=True)
    competencias = CompetenciaSerializer(many=True, read_only=True)
    contato = serializers.SerializerMethodField()

    class Meta:
        model = Perfil
        fields = ["username", "nome", "curso", "polo", "bio", "interesses", "competencias", "contato"]

    def get_contato(self, obj):
        request = self.context.get("request")
        if request and services.pode_ver_contato(request.user, obj.usuario):
            return obj.contato or obj.usuario.email
        return None


class ProjetoSerializer(serializers.ModelSerializer):
    autor = AutorSerializer(read_only=True)
    competencias_desejadas = CompetenciaSerializer(many=True, read_only=True)
    competencias_ids = serializers.PrimaryKeyRelatedField(
        source="competencias_desejadas", queryset=Competencia.objects.all(),
        many=True, write_only=True, required=False,
    )
    vagas_restantes = serializers.IntegerField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="api:projeto-detail")

    class Meta:
        model = Projeto
        fields = [
            "id", "url", "titulo", "resumo", "descricao", "objetivo", "tipo", "status",
            "vagas", "vagas_restantes", "autor", "competencias_desejadas", "competencias_ids",
            "criado_em", "atualizado_em",
        ]
        read_only_fields = ["criado_em", "atualizado_em"]


class InteresseSerializer(serializers.ModelSerializer):
    estudante = AutorSerializer(read_only=True)
    projeto_titulo = serializers.CharField(source="projeto.titulo", read_only=True)

    class Meta:
        model = Interesse
        fields = ["id", "projeto", "projeto_titulo", "estudante", "mensagem", "status", "criado_em", "respondido_em"]
        read_only_fields = ["projeto", "status", "criado_em", "respondido_em"]


# ---------- Permissões ----------

class EhAutorOuSomenteLeitura(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.autor_id == request.user.pk


def _erro(exc):
    return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)


# ---------- ViewSets ----------

class CompetenciaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Competencia.objects.all()
    serializer_class = CompetenciaSerializer
    pagination_class = None


class ProjetoViewSet(viewsets.ModelViewSet):
    """Projetos publicados. Filtros: ?q=, ?competencia=<slug>, ?tipo=, ?abertos=true"""

    serializer_class = ProjetoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, EhAutorOuSomenteLeitura]

    def get_queryset(self):
        base = Projeto.objects.select_related("autor").prefetch_related("competencias_desejadas")
        params = self.request.query_params.copy()
        if params.get("abertos", "").lower() in {"true", "1", "sim"}:
            params["abertos"] = "on"
        return filtrar_projetos(params, base)[1]

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def interesse(self, request, pk=None):
        """Manifesta interesse em participar. Corpo: {"mensagem": "..."}"""
        projeto = self.get_object()
        try:
            interesse = services.manifestar_interesse(projeto, request.user, str(request.data.get("mensagem", ""))[:500])
        except DjangoValidationError as exc:
            return _erro(exc)
        return Response(InteresseSerializer(interesse).data, status=status.HTTP_201_CREATED)


class InteresseViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Interesses que eu manifestei e os recebidos nos meus projetos."""

    serializer_class = InteresseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        return Interesse.objects.filter(Q(estudante=u) | Q(projeto__autor=u)).select_related("projeto", "estudante")

    def perform_destroy(self, instance):
        try:
            services.cancelar_interesse(instance, self.request.user)
        except DjangoPermissionDenied:
            raise PermissionDenied("Somente quem manifestou o interesse pode retirá-lo.")
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"detail": exc.messages[0]})

    @action(detail=True, methods=["post"])
    def responder(self, request, pk=None):
        """Autor aceita ou recusa. Corpo: {"acao": "aceitar" | "recusar"}"""
        interesse = self.get_object()
        acao = request.data.get("acao")
        if acao not in {"aceitar", "recusar"}:
            return Response({"detail": "Informe acao = 'aceitar' ou 'recusar'."}, status=400)
        try:
            services.responder_interesse(interesse, request.user, acao == "aceitar")
        except DjangoPermissionDenied:
            raise PermissionDenied("Somente o autor do projeto pode responder.")
        except DjangoValidationError as exc:
            return _erro(exc)
        return Response(InteresseSerializer(interesse).data)


class PerfilViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PerfilSerializer
    lookup_field = "usuario__username"
    lookup_url_kwarg = "username"

    def get_queryset(self):
        qs = Perfil.objects.select_related("usuario").prefetch_related("competencias")
        competencia = self.request.query_params.get("competencia")
        if competencia:
            qs = qs.filter(competencias__slug=competencia)
        return qs
