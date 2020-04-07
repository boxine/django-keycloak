import mock

from datetime import datetime

from django.test import TestCase, override_settings
from keycloak.openid_connect import KeycloakOpenidConnect

from django_keycloak.factories import ClientFactory, \
    OpenIdConnectProfileFactory, UserFactory
from django_keycloak.tests.mixins import MockTestCaseMixin

import django_keycloak.services.oidc_profile


class ServicesOpenIDProfileGetOrCreateFromIdTokenTestCase(
        MockTestCaseMixin, TestCase):

    def setUp(self):
        self.client = ClientFactory(
            realm___certs='{}',
            realm___well_known_oidc='{"issuer": "https://issuer"}'
        )
        self.client.openid_api_client = mock.MagicMock(
            spec_set=KeycloakOpenidConnect)
        self.client.openid_api_client.well_known = {
            'id_token_signing_alg_values_supported': ['signing-alg']
        }
        self.client.openid_api_client.decode_token.return_value = {
            'sub': 'some-sub',
            'email': 'test@example.com',
            'given_name': 'Some given name',
            'family_name': 'Some family name'
        }

    def test_create_with_new_user_new_profile(self):
        """
        Case: oidc profile is requested based on a provided id token.
        The user and profile do not exist yet.
        Expected: oidc profile and user are created with information from
        the id token.
        """
        profile = django_keycloak.services.oidc_profile. \
            get_or_create_from_id_token(
                client=self.client, id_token='some-id-token'
            )

        self.client.openid_api_client.decode_token.assert_called_with(
            token='some-id-token',
            key=dict(),
            algorithms=['signing-alg'],
            issuer='https://issuer'
        )

        self.assertEqual(profile.sub, 'some-sub')
        self.assertEqual(profile.user.username, 'some-sub')
        self.assertEqual(profile.user.email, 'test@example.com')
        self.assertEqual(profile.user.first_name, 'Some given name')
        self.assertEqual(profile.user.last_name, 'Some family name')

    def test_update_with_existing_profile_new_user(self):
        """
        Case: oidc profile is requested based on a provided id token.
        The profile exists, but the user doesn't.
        Expected: oidc user is created with information from the id token
        and linked to the profile.
        """
        existing_profile = OpenIdConnectProfileFactory(
            access_token='access-token',
            expires_before=datetime(2018, 3, 5, 1, 0, 0),
            refresh_token='refresh-token',
            sub='some-sub'
        )

        profile = django_keycloak.services.oidc_profile. \
            get_or_create_from_id_token(
                client=self.client, id_token='some-id-token'
            )

        self.client.openid_api_client.decode_token.assert_called_with(
            token='some-id-token',
            key=dict(),
            algorithms=['signing-alg'],
            issuer='https://issuer'
        )

        self.assertEqual(profile.sub, 'some-sub')
        self.assertEqual(profile.pk, existing_profile.pk)
        self.assertEqual(profile.user.username, 'some-sub')
        self.assertEqual(profile.user.email, 'test@example.com')
        self.assertEqual(profile.user.first_name, 'Some given name')
        self.assertEqual(profile.user.last_name, 'Some family name')

    def test_create_with_existing_user_new_profile(self):
        """
        Case: oidc profile is requested based on a provided id token.
        The user exists, but the profile doesn't.
        Expected: oidc profile is created and user is linked to the profile.
        """
        existing_user = UserFactory(
            username='some-sub'
        )

        profile = django_keycloak.services.oidc_profile.\
            get_or_create_from_id_token(
                client=self.client, id_token='some-id-token'
            )

        self.client.openid_api_client.decode_token.assert_called_with(
            token='some-id-token',
            key=dict(),
            algorithms=['signing-alg'],
            issuer='https://issuer'
        )

        self.assertEqual(profile.sub, 'some-sub')
        self.assertEqual(profile.user.pk, existing_user.pk)
        self.assertEqual(profile.user.username, 'some-sub')
        self.assertEqual(profile.user.email, 'test@example.com')
        self.assertEqual(profile.user.first_name, 'Some given name')
        self.assertEqual(profile.user.last_name, 'Some family name')

    @override_settings(KEYCLOAK_USERNAME_TOKEN_ATTRIBUTE='email')
    def test_create_with_existing_user_new_profile_different_token_attribute(self):

        client = ClientFactory(realm___certs='{}',
                               realm___well_known_oidc='{"issuer": "https://issuer"}')

        client.openid_api_client = mock.MagicMock(spec_set=KeycloakOpenidConnect)
        client.openid_api_client.well_known = {
            'id_token_signing_alg_values_supported': ['signing-alg']
        }
        client.openid_api_client.decode_token.return_value = {
            'sub': 'some-sub',
            'email': 'test@example.com',
            'given_name': 'Some given name',
            'family_name': 'Some family name'
        }

        existing_user = UserFactory(username='test@example.com')

        profile = django_keycloak.services.oidc_profile.\
            get_or_create_from_id_token(
                client=client, id_token='some-id-token'
            )
        client.openid_api_client.decode_token.assert_called_with(
            token='some-id-token',
            key=dict(),
            algorithms=['signing-alg'],
            issuer='https://issuer'
        )

        self.assertEqual(profile.sub, 'some-sub')
        self.assertEqual(profile.user.pk, existing_user.pk)
        self.assertEqual(profile.user.username, 'test@example.com')
        self.assertEqual(profile.user.email, 'test@example.com')
        self.assertEqual(profile.user.first_name, 'Some given name')
        self.assertEqual(profile.user.last_name, 'Some family name')

    @override_settings(KEYCLOAK_USERNAME_TOKEN_ATTRIBUTE='foo.bar')
    def test_create_with_existing_user_new_profile_token_attribute_nested(self):

        client = ClientFactory(realm___certs='{}',
                               realm___well_known_oidc='{"issuer": "https://issuer"}')

        client.openid_api_client = mock.MagicMock(spec_set=KeycloakOpenidConnect)
        client.openid_api_client.well_known = {
            'id_token_signing_alg_values_supported': ['signing-alg']
        }
        client.openid_api_client.decode_token.return_value = {
            'sub': 'some-sub',
            'email': 'test@example.com',
            'given_name': 'Some given name',
            'family_name': 'Some family name',
            'foo': {
                'bar': 'joe.random'
            }
        }

        existing_user = UserFactory(username='joe.random')

        profile = django_keycloak.services.oidc_profile.\
            get_or_create_from_id_token(
                client=client, id_token='some-id-token'
            )
        client.openid_api_client.decode_token.assert_called_with(
            token='some-id-token',
            key=dict(),
            algorithms=['signing-alg'],
            issuer='https://issuer'
        )

        self.assertEqual(profile.sub, 'some-sub')
        self.assertEqual(profile.user.pk, existing_user.pk)
        self.assertEqual(profile.user.username, 'joe.random')
        self.assertEqual(profile.user.email, 'test@example.com')
        self.assertEqual(profile.user.first_name, 'Some given name')
        self.assertEqual(profile.user.last_name, 'Some family name')

    @override_settings(KEYCLOAK_USERNAME_FIELD='email')
    def test_create_with_existing_user_new_profile_different_username_field(self):

        client = ClientFactory(realm___certs='{}',
                               realm___well_known_oidc='{"issuer": "https://issuer"}')

        client.openid_api_client = mock.MagicMock(spec_set=KeycloakOpenidConnect)
        client.openid_api_client.well_known = {
            'id_token_signing_alg_values_supported': ['signing-alg']
        }
        client.openid_api_client.decode_token.return_value = {
            'sub': 'test@example.com',
            'email': 'doesnotexist@example.com',
            'given_name': 'Some given name',
            'family_name': 'Some family name'
        }

        existing_user = UserFactory(username='some-sub', email='test@example.com')

        profile = django_keycloak.services.oidc_profile.\
            get_or_create_from_id_token(
                client=client, id_token='some-id-token'
            )
        client.openid_api_client.decode_token.assert_called_with(
            token='some-id-token',
            key=dict(),
            algorithms=['signing-alg'],
            issuer='https://issuer'
        )

        self.assertEqual(profile.sub, 'test@example.com')
        self.assertEqual(profile.user.pk, existing_user.pk)
        self.assertEqual(profile.user.username, 'test@example.com')
        self.assertEqual(profile.user.email, 'doesnotexist@example.com')
        self.assertEqual(profile.user.first_name, 'Some given name')
        self.assertEqual(profile.user.last_name, 'Some family name')

    def test_create_with_existing_user_existing_profile(self):
        """
        Case: oidc profile is requested based on a provided id token.
        The user and profile already exist.
        Expected: existing oidc profile is returned with existing user linked
        to it.
        """
        existing_user = UserFactory(
            username='some-sub'
        )

        existing_profile = OpenIdConnectProfileFactory(
            access_token='access-token',
            expires_before=datetime(2018, 3, 5, 1, 0, 0),
            refresh_token='refresh-token',
            sub='some-sub'
        )

        profile = django_keycloak.services.oidc_profile.\
            get_or_create_from_id_token(
                client=self.client, id_token='some-id-token'
            )

        self.client.openid_api_client.decode_token.assert_called_with(
            token='some-id-token',
            key=dict(),
            algorithms=['signing-alg'],
            issuer='https://issuer'
        )

        self.assertEqual(profile.pk, existing_profile.pk)
        self.assertEqual(profile.sub, 'some-sub')
        self.assertEqual(profile.user.pk, existing_user.pk)
        self.assertEqual(profile.user.username, 'some-sub')
        self.assertEqual(profile.user.email, 'test@example.com')
        self.assertEqual(profile.user.first_name, 'Some given name')
        self.assertEqual(profile.user.last_name, 'Some family name')

    @override_settings(KEYCLOAK_USERPROFILE_FACTORY='django_keycloak.tests.services.oidc_profile.'
                                                    'test_get_or_create_from_id_token.'
                                                    'user_profile_factory_dummy')
    def test_create_new_profile_with_factory(self):

        profile = django_keycloak.services.oidc_profile. \
            get_or_create_from_id_token(
                client=self.client, id_token='some-id-token'
            )

        self.client.openid_api_client.decode_token.assert_called_with(
            token='some-id-token',
            key=dict(),
            algorithms=['signing-alg'],
            issuer='https://issuer'
        )

        self.assertEqual(profile.sub, 'some-sub')
        self.assertEqual(profile.user.username, 'some-sub')
        self.assertEqual(profile.user.email, 'test@example.com')
        self.assertEqual(profile.user.first_name, 'Firstname changed in factory')
        self.assertEqual(profile.user.last_name, 'Lastname changed in factory')


def user_profile_factory_dummy(defaults, token):
    defaults['first_name'] = 'Firstname changed in factory'
    defaults['last_name'] = 'Lastname changed in factory'
    return defaults
