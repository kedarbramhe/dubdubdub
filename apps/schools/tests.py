from django.utils import unittest
from django.test import TestCase
from django.test.client import Client
import json

class ApiTestCase(unittest.TestCase):
   
    def setUp(self):
        self.c = Client()
 
    def test_passing_test(self):
        x = 2
        self.assertEquals(x, 2, "2 is equal to 2")
   
    def test_api_schools_list(self):
        response = self.c.get("/api/v1/schools/list?bounds=77.54537736775214,12.950457093960514,77.61934126017755,13.022529216896507")
        self.assertEqual(response.status_code, 200, "schools list status code is 200")
        results = json.loads(response.content)
        self.assertEqual(len(results['features']), 50, "got 50 schools as first page")
        sample_school = results['features'][0]
        self.assertTrue(sample_school['properties'].has_key('id'), "has a property called id")
        self.assertTrue(sample_school['properties'].has_key('name'), "has a property called name")

    def test_api_schools_info(self):
        response = self.c.get("/api/v1/schools/info")
        self.assertEqual(response.status_code, 200, "schools info status code is 200")
        results = json.loads(response.content)
        self.assertEqual(len(results['features']), 50, "got 50 schools as first page")
        sample_school = results['features'][0]
        self.assertTrue(sample_school['properties'].has_key('management'), 'has a property called management')
        self.assertTrue(sample_school['properties'].has_key('category'), 'has a property called category')
        self.assertTrue(sample_school['properties'].has_key('address'), 'has a property called address')
        self.assertTrue(sample_school['properties'].has_key('dise_code'), "has a property called dise_code")
        response_page2 = self.c.get("/api/v1/schools/info?page=2")
        self.assertEqual(response_page2.status_code, 200, "schools info page 2 status code is 200")
        results_page2 = json.loads(response_page2.content)
        self.assertEqual(len(results_page2['features']), 50, "got 50 schools as second page")
        sample_school_2 = results_page2['features'][0]
        school1id = sample_school['properties']['id']
        school2id = sample_school_2['properties']['id']
        self.assertFalse(school1id == school2id, "page 2 differs from page 1")