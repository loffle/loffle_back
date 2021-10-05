from django.contrib.auth import user_logged_in
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_text, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from account.models import User
from account.serializers import UserSerializer


class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, create = Token.objects.get_or_create(user=user)

        user_logged_in.send(sender=user.__class__, request=request, user=user)

        return Response({
            'token': token.key,
            'nickname': user.username,
        })


class LogoutView(APIView):
    def get(self, request, format=None):
        if request.auth is not None:
            request.auth.delete()
            return Response({'detail': '로그아웃 되었습니다.'}, status=HTTP_200_OK)
        else:
            return Response({'detail': '로그인 상태가 아닙니다.'}, status=HTTP_401_UNAUTHORIZED)


class SignUpView(CreateAPIView):
    model = User
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        # 유저 저장(is_active=False)
        result = super().post(request, *args, **kwargs)

        # 이메일 전송
        user = User.objects.get(email=request.data['email'])
        url_kwargs = {
            'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': PasswordResetTokenGenerator().make_token(user),
        }

        activate_url = reverse('activate', kwargs=url_kwargs, request=request)

        subject = _(f'{user.username}님, 계정을 활성화해주세요.')
        message = _(f'링크에 접속하여 계정을 활성화해주세요.\n\n{activate_url}')

        email = EmailMessage(subject, message, to=[user.email])
        email.send()
        return result


class ActivateView(APIView):

    def get(self, request, uidb64, token):
        # uid 디코딩 검증
        try:
            user_pk = force_text(urlsafe_base64_decode(uidb64))
        except DjangoUnicodeDecodeError:
            return Response({'detail': 'uid 값이 올바르지 않습니다.'}, status=HTTP_400_BAD_REQUEST)

        # 사용자 pk 검증
        try:
            user = User.objects.get(pk=user_pk)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': '존재하지 않는 사용자입니다.'}, status=HTTP_404_NOT_FOUND)

        # 토큰 검증
        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({'detail': '토큰값이 올바르지 않습니다.'}, status=HTTP_400_BAD_REQUEST)

        # 계정 활성화 처리
        user.is_active = True
        user.save()
        return Response(status=HTTP_200_OK)


class CheckUserView(APIView):
    """
    사용자 정보 검증
    - email
    - username
    - phone
    """

    def post(self, request):
        result = {}

        check_list = ['email', 'username', 'phone']

        for col in check_list:
            value = request.POST.get(col, '')
            if value:
                result[col + '_exist'] = User.objects.filter(**{col: value}).exists()

        if not result:
            return Response({'detail': '이메일 또는 닉네임 또는 핸드폰 값이 필요합니다.'}, status=HTTP_400_BAD_REQUEST)

        return Response(result, status=HTTP_200_OK)
