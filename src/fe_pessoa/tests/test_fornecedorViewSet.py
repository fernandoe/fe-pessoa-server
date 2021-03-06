import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_jwt.settings import api_settings

from fe_pessoa.models import Fornecedor
from fe_pessoa.tests.factories import FornecedorFactory, EntityFactory
from .factories import UserFactory

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class TestFornecedorViewSet(APITestCase):

    def setUp(self):
        self.entity = EntityFactory()
        self.user = UserFactory(entity=self.entity)

        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        self.fornecedor = FornecedorFactory(entidade=self.entity)

    def compare_entity(self, entity, result):
        self.assertEqual(7, len(result))
        self.assertEqual(str(entity.uuid), result.get('uuid'))
        self.assertTrue(result.get('created_at', None))
        self.assertTrue(result.get('updated_at', None))
        self.assertEqual(entity.nome, result.get('nome'))
        self.assertEqual(entity.email, result.get('email'))
        self.assertEqual(entity.telefone_celular, result.get('telefone_celular'))
        self.assertEqual(str(entity.endereco), result.get('endereco'))

    def test_get_200(self):
        response = self.client.get(reverse('fornecedores-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, response.data['count'])

    def test_get_transiente_true(self):
        fornecedor = FornecedorFactory(entidade=self.entity, transiente=True)
        response = self.client.get(reverse('fornecedores-detail', args=(fornecedor.uuid,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(fornecedor.uuid), response.data.get('uuid'))
        self.assertTrue(fornecedor.transiente)

    def test_get_transiente_false(self):
        fornecedor = FornecedorFactory(entidade=self.entity, transiente=False)
        response = self.client.get(reverse('fornecedores-detail', args=(fornecedor.uuid,)))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(fornecedor.uuid), response.data.get('uuid'))
        self.assertFalse(fornecedor.transiente)

    def test_put(self):
        fornecedor = Fornecedor.objects.create(entidade=self.entity)
        self.assertTrue(fornecedor.transiente)
        response = self.client.put(reverse('fornecedores-detail', args=(fornecedor.uuid,)), {
            'nome': 'Cliente de teste (put)',
            'telefone_celular': '92832466',
            'endereco': str(uuid.uuid4())
        })
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        entity = Fornecedor.objects.get(pk=response.data.get('uuid'))
        result = response.data
        self.compare_entity(entity, result)
        self.assertEqual(self.entity, entity.entidade)
        self.assertFalse(entity.transiente)

    def test_patch_endereco(self):
        endereco = str(uuid.uuid4())
        response = self.client.patch(reverse('fornecedores-detail', args=(self.fornecedor.uuid,)), {
            'endereco': endereco
        })
        entity = Fornecedor.objects.get(pk=response.data.get('uuid'))
        self.assertEqual(endereco, response.data.get('endereco'))
        self.assertEqual(endereco, str(entity.endereco))

    def test_uudis(self):
        f1 = FornecedorFactory(entidade=self.entity)
        f2 = FornecedorFactory(entidade=self.entity)
        FornecedorFactory(entidade=self.entity, transiente=True)
        FornecedorFactory.create_batch(3)
        uuids = '%s,%s' % (f1.uuid, f2.uuid)
        response = self.client.get(reverse('fornecedores-list'), {
            'uuids': uuids
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, response.data['count'])
        results = response.data['results']
        self.assertSequenceEqual(
            sorted([str(f1.uuid), str(f2.uuid)]),
            sorted([results[0].get('uuid'), results[1].get('uuid')]))

    def test_query(self):
        cliente = FornecedorFactory(nome="Cliente (123)", entidade=self.entity)
        FornecedorFactory(entidade=self.entity, transiente=True)
        FornecedorFactory.create_batch(3)
        response = self.client.get(reverse('fornecedores-list'), {
            'query': '123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, response.data['count'])
        results = response.data['results']
        self.assertEqual(str(cliente.uuid), results[0].get('uuid'))
        self.assertEqual(str(cliente.nome), results[0].get('nome'))

    def test_post_transiente_true(self):
        response = self.client.post(reverse('fornecedores-list'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        fornecedor = Fornecedor.objects.get(pk=response.data.get('uuid'))
        self.assertIsNotNone(fornecedor)
        self.assertEqual(False, fornecedor.transiente)

    def test_post(self):
        response = self.client.post(reverse('fornecedores-list'), {
            'nome': 'Fornecedor de teste (post)',
            'telefone_celular': '92832466',
            'endereco': str(uuid.uuid4())
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        entity = Fornecedor.objects.get(pk=response.data.get('uuid'))
        result = response.data
        self.compare_entity(entity, result)
        self.assertEqual(self.entity, entity.entidade)
        self.assertFalse(entity.transiente)
